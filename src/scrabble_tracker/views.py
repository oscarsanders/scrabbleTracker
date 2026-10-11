"""Plain read-only view objects built from ORM entities.

The UI renders these instead of live ORM objects, so rendering is pure
(testable without a database) and cannot trigger lazy loads after the
session is closed.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from scrabble_tracker.models import (
    STATUS_FINISHED,
    Game,
    GamePlayer,
    User,
)


@dataclass(frozen=True)
class TurnRow:
    player: str
    turn_type: str
    word: str | None
    points: int


@dataclass(frozen=True)
class PlayerScore:
    player_id: int
    name: str
    score: int
    scrabbles: int
    turns: int
    penalty: int
    bonus: int
    remaining_tiles: str


@dataclass(frozen=True)
class GameView:
    game_id: int
    mode: str
    language: str
    status: str
    average_score: float
    ranking: tuple[PlayerScore, ...]
    roster: tuple[tuple[int, str], ...]  # (player_id, name) in turn order
    turns: tuple[TurnRow, ...]  # newest first

    @property
    def is_finished(self) -> bool:
        return self.status == STATUS_FINISHED


@dataclass(frozen=True)
class HistoryRow:
    game_id: int
    date: str
    mode: str
    language: str
    final_score: int
    position: int
    players: int


@dataclass(frozen=True)
class ProfileView:
    username: str
    total_games: int
    average_score: float
    best_score: int
    total_scrabbles: int
    wins: int


@dataclass(frozen=True)
class UserRow:
    user_id: int
    username: str
    is_admin: bool
    created: str


@dataclass(frozen=True)
class ActiveGame:
    game_id: int
    label: str


def build_game_view(game: Game) -> GameView:
    """Snapshot of a game for display."""
    ranking = tuple(
        PlayerScore(
            player_id=player.id,
            name=player.display_name,
            score=score,
            scrabbles=player.scrabble_count,
            turns=len(player.turns),
            penalty=player.tile_penalty or 0,
            bonus=player.tile_bonus or 0,
            remaining_tiles=player.remaining_tiles or "",
        )
        for player, score in game.ranking()
    )
    roster = tuple((p.id, p.display_name) for p in game.players)

    all_turns = sorted(
        ((p, t) for p in game.players for t in p.turns),
        key=lambda pair: (pair[1].created_at, pair[1].id),
        reverse=True,
    )
    turns = tuple(
        TurnRow(
            player=p.display_name,
            turn_type=t.turn_type,
            word=t.word,
            points=t.points,
        )
        for p, t in all_turns
    )
    return GameView(
        game_id=game.id,
        mode=game.mode,
        language=game.language,
        status=game.status,
        average_score=game.average_score(),
        ranking=ranking,
        roster=roster,
        turns=turns,
    )


def _finished_sort_key(participation: GamePlayer):
    game = participation.game
    return game.finished_at or game.created_at


def build_history(user: User) -> list[HistoryRow]:
    """Finished games of ``user``, newest first (RF-04)."""
    rows: list[HistoryRow] = []
    participations = sorted(
        user.finished_participations(), key=_finished_sort_key, reverse=True
    )
    for participation in participations:
        game = participation.game
        ranking = game.ranking()
        position = next(
            (
                i
                for i, (p, _) in enumerate(ranking, start=1)
                if p.id == participation.id
            ),
            len(ranking),
        )
        when = game.finished_at or game.created_at
        rows.append(
            HistoryRow(
                game_id=game.id,
                date=when.strftime("%Y-%m-%d"),
                mode=game.mode,
                language=game.language,
                final_score=participation.final_score,
                position=position,
                players=len(ranking),
            )
        )
    return rows


def build_profile(user: User) -> ProfileView:
    """Aggregate statistics for the profile page (RF-03)."""
    return ProfileView(
        username=user.username,
        total_games=user.total_games,
        average_score=user.average_score,
        best_score=user.best_score,
        total_scrabbles=user.total_scrabbles,
        wins=user.wins,
    )


def build_user_rows(users: Iterable[User]) -> list[UserRow]:
    return [
        UserRow(
            user_id=u.id,
            username=u.username,
            is_admin=u.is_admin,
            created=u.created_at.strftime("%Y-%m-%d"),
        )
        for u in users
    ]


def build_active_games(games: Iterable[Game]) -> list[ActiveGame]:
    """Label games in progress so the user can pick one to resume."""
    result = []
    for game in games:
        names = ", ".join(p.display_name for p in game.players)
        result.append(
            ActiveGame(
                game_id=game.id,
                label=f"Game #{game.id} · {names} · {game.language.upper()}",
            )
        )
    return result
