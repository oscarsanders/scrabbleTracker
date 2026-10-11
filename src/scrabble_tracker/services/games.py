"""Game use cases: create, play, undo, finish (RF-06 .. RF-15)."""

from __future__ import annotations

import logging
from collections.abc import Mapping

from sqlalchemy import select
from sqlalchemy.orm import Session

from scrabble_tracker.errors import DomainError, NotFoundError
from scrabble_tracker.models import (
    GAME_MODES,
    STATUS_FINISHED,
    STATUS_IN_PROGRESS,
    TURN_TYPES,
    ZERO_POINT_TURN_TYPES,
    Game,
    GamePlayer,
    Turn,
    User,
    utcnow,
)
from scrabble_tracker.rules import compute_closing
from scrabble_tracker.services.accounts import find_user
from scrabble_tracker.tiles import SUPPORTED_LANGUAGES

logger = logging.getLogger("scrabble_tracker.games")

#: Official game supports two to four players.
MAX_PLAYERS = 4
MAX_NAME_LENGTH = 64
MAX_WORD_LENGTH = 64
MAX_RACK_LENGTH = 32


def parse_player_names(raw: str) -> list[str]:
    """Split a comma-separated string into trimmed, non-empty names."""
    return [part.strip() for part in (raw or "").split(",") if part.strip()]


def start_game(
    session: Session,
    *,
    creator: User,
    mode: str,
    language: str,
    other_players: str = "",
) -> Game:
    """Create a game and its players (RF-06, RF-11).

    In ``individual`` mode only the creator plays. In ``multiplayer``
    mode ``other_players`` is a comma-separated list of names; names that
    match a registered user (case-insensitive) are linked to that
    account, the rest are guests. The creator is always a participant.

    Raises:
        DomainError: invalid mode/language, duplicate or over-long names,
            fewer than two or more than :data:`MAX_PLAYERS` players.
    """
    if mode not in GAME_MODES:
        raise DomainError(f"Invalid game mode: {mode!r}.")
    if language not in SUPPORTED_LANGUAGES:
        raise DomainError("Please choose a valid tile language.")

    if mode == "individual":
        names = [creator.username]
    else:
        names = parse_player_names(other_players)
        if creator.username.lower() not in {n.lower() for n in names}:
            names.insert(0, creator.username)

    if len({n.lower() for n in names}) != len(names):
        raise DomainError("Player names must be unique.")
    if mode == "multiplayer" and len(names) < 2:
        raise DomainError("Multiplayer games need at least two players.")
    if len(names) > MAX_PLAYERS:
        raise DomainError(f"A game supports at most {MAX_PLAYERS} players.")
    if any(len(n) > MAX_NAME_LENGTH for n in names):
        raise DomainError(f"Player names are limited to {MAX_NAME_LENGTH} characters.")

    # Resolve accounts first: queries after the new objects exist could
    # trigger an autoflush of a half-built game.
    resolved = [(name, find_user(session, name)) for name in names]

    game = Game(created_by=creator, mode=mode, language=language)
    for order, (name, registered) in enumerate(resolved):
        game.players.append(
            GamePlayer(
                user=registered,
                guest_name=None if registered else name,
                turn_order=order,
            )
        )
    session.add(game)
    session.flush()
    logger.info(
        "game_created",
        extra={"game_id": game.id, "mode": mode, "players": len(names)},
    )
    return game


def get_game_for_user(session: Session, game_id: int | None, user: User) -> Game:
    """Fetch a game the user participates in or created.

    Missing games and games the user may not see raise the *same*
    :class:`NotFoundError` so ids cannot be probed.
    """
    game = session.get(Game, game_id) if game_id is not None else None
    if game is None:
        raise NotFoundError("Game not found.")
    is_participant = any(p.user_id == user.id for p in game.players)
    if not is_participant and game.created_by_id != user.id:
        raise NotFoundError("Game not found.")
    return game


def _require_in_progress(game: Game) -> None:
    if game.status == STATUS_FINISHED:
        raise DomainError("This game is already finished.")


def _find_player(game: Game, player_id: int | None) -> GamePlayer:
    for player in game.players:
        if player.id == player_id:
            return player
    raise NotFoundError("Player not found in this game.")


def add_turn(
    session: Session,
    *,
    game: Game,
    player_id: int | None,
    turn_type: str,
    word: str | None,
    points: int,
) -> Turn:
    """Record a move for a player (RF-07, RF-08).

    Foul, pass and exchange never score, so their points are forced to 0.
    The pass and exchange moves carry no word.
    """
    _require_in_progress(game)
    player = _find_player(game, player_id)
    if turn_type not in TURN_TYPES:
        raise DomainError(f"Invalid move type: {turn_type!r}.")
    if not isinstance(points, int) or isinstance(points, bool) or points < 0:
        raise DomainError("Points must be a whole number, zero or greater.")
    clean_word = (word or "").strip() or None
    if clean_word is not None and len(clean_word) > MAX_WORD_LENGTH:
        raise DomainError(f"Words are limited to {MAX_WORD_LENGTH} characters.")

    if turn_type in ZERO_POINT_TURN_TYPES:
        points = 0
    if turn_type in ("pass", "exchange"):
        clean_word = None

    # Build through the relationship so ``player.turns`` stays consistent
    # in memory without needing a refresh.
    turn = Turn(
        player=player,
        sequence=len(player.turns) + 1,
        turn_type=turn_type,
        word=clean_word,
        points=points,
    )
    session.add(turn)
    session.flush()
    logger.info(
        "turn_added",
        extra={"game_id": game.id, "player_id": player.id, "turn_type": turn_type},
    )
    return turn


def undo_last_turn(session: Session, *, game: Game, player_id: int | None) -> bool:
    """Remove the player's most recent move. Returns ``False`` if none."""
    _require_in_progress(game)
    player = _find_player(game, player_id)
    if not player.turns:
        return False
    player.turns.remove(player.turns[-1])  # delete-orphan removes the row
    session.flush()
    logger.info("turn_undone", extra={"game_id": game.id, "player_id": player.id})
    return True


def finish_game(
    session: Session, *, game: Game, remaining_by_player: Mapping[int, str]
) -> None:
    """Apply the closing rule and mark the game finished (RF-12 .. RF-14).

    ``remaining_by_player`` maps ``GamePlayer.id`` to the tiles that
    player still holds; omitted players count as having none.
    """
    _require_in_progress(game)
    racks = {p.id: (remaining_by_player.get(p.id) or "") for p in game.players}
    if any(len(rack.strip()) > MAX_RACK_LENGTH for rack in racks.values()):
        raise DomainError(
            f"Remaining tiles are limited to {MAX_RACK_LENGTH} characters per player."
        )

    adjustments = compute_closing(racks, game.language)
    for player in game.players:
        adjustment = adjustments[player.id]
        player.remaining_tiles = adjustment.remaining_tiles
        player.tile_penalty = adjustment.penalty
        player.tile_bonus = adjustment.bonus
        player.finished_rack_first = adjustment.emptied_rack

    game.status = STATUS_FINISHED
    game.finished_at = utcnow()
    session.flush()
    logger.info("game_finished", extra={"game_id": game.id})


def list_games(session: Session, user: User, status: str) -> list[Game]:
    """Games of ``user`` with the given status, newest first."""
    stmt = (
        select(Game)
        .join(GamePlayer, GamePlayer.game_id == Game.id)
        .where(GamePlayer.user_id == user.id, Game.status == status)
        .order_by(Game.created_at.desc(), Game.id.desc())
    )
    return list(session.scalars(stmt).unique())


def list_active_games(session: Session, user: User) -> list[Game]:
    return list_games(session, user, STATUS_IN_PROGRESS)


def list_finished_games(session: Session, user: User) -> list[Game]:
    return list_games(session, user, STATUS_FINISHED)


__all__ = [
    "MAX_PLAYERS",
    "add_turn",
    "finish_game",
    "get_game_for_user",
    "list_active_games",
    "list_finished_games",
    "list_games",
    "parse_player_names",
    "start_game",
    "undo_last_turn",
]
