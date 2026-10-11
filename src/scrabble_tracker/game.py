"""In-memory model of ONE Scrabble game.

Nothing here touches a database, a file or global state: a :class:`Game`
is a plain object that the UI keeps in the visitor's own browser session.
When the session ends the game is gone, by design (ADR-0005).

Only the standard library and sibling pure modules are used, so this
module is unit-tested without any framework.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from scrabble_tracker.errors import DomainError
from scrabble_tracker.rules import compute_closing
from scrabble_tracker.tiles import SUPPORTED_LANGUAGES

TURN_TYPES: tuple[str, ...] = ("normal", "scrabble", "foul", "pass", "exchange")
#: Move types that never score points, by the rules of the game.
ZERO_POINT_TURN_TYPES: tuple[str, ...] = ("foul", "pass", "exchange")

MAX_PLAYERS = 4
MAX_NAME_LENGTH = 32
MAX_WORD_LENGTH = 64
MAX_RACK_LENGTH = 32
#: Bounds the memory a single visitor can use.
MAX_TURNS = 500


@dataclass(frozen=True)
class Turn:
    """One recorded move. ``player`` is the index in ``Game.players``."""

    player: int
    turn_type: str
    word: str | None
    points: int


@dataclass
class Player:
    """A participant plus the adjustments applied when the game closes."""

    name: str
    remaining_tiles: str = ""
    penalty: int = 0
    bonus: int = 0


def parse_player_names(raw: str) -> list[str]:
    """Split a comma-separated string into trimmed, non-empty names."""
    return [part.strip() for part in (raw or "").split(",") if part.strip()]


class Game:
    """State and rules of a single game (RF-01 .. RF-12)."""

    def __init__(self, language: str, names: Sequence[str]) -> None:
        if language not in SUPPORTED_LANGUAGES:
            raise DomainError("Please choose a valid tile language.")
        if not names:
            raise DomainError("Enter at least one player name.")
        if len(names) > MAX_PLAYERS:
            raise DomainError(f"A game supports at most {MAX_PLAYERS} players.")
        if len({n.lower() for n in names}) != len(names):
            raise DomainError("Player names must be unique.")
        if any(len(n) > MAX_NAME_LENGTH for n in names):
            raise DomainError(f"Names are limited to {MAX_NAME_LENGTH} characters.")

        self.language = language
        self.players: list[Player] = [Player(name) for name in names]
        self.turns: list[Turn] = []
        self.finished = False

    # -- guards ---------------------------------------------------------
    def _require_open(self) -> None:
        if self.finished:
            raise DomainError("This game is already finished.")

    def _require_player(self, index: object) -> int:
        if (
            not isinstance(index, int)
            or isinstance(index, bool)
            or not 0 <= index < len(self.players)
        ):
            raise DomainError("Choose a player.")
        return index

    # -- moves ----------------------------------------------------------
    def add_turn(
        self, player: object, turn_type: str, word: str | None, points: int
    ) -> Turn:
        """Record a move. Foul, pass and exchange are forced to 0 points."""
        self._require_open()
        index = self._require_player(player)
        if turn_type not in TURN_TYPES:
            raise DomainError("Invalid move type.")
        if not isinstance(points, int) or isinstance(points, bool) or points < 0:
            raise DomainError("Points must be a whole number, zero or greater.")
        clean_word = (word or "").strip() or None
        if clean_word is not None and len(clean_word) > MAX_WORD_LENGTH:
            raise DomainError(f"Words are limited to {MAX_WORD_LENGTH} characters.")
        if len(self.turns) >= MAX_TURNS:
            raise DomainError(f"A game is limited to {MAX_TURNS} moves.")

        if turn_type in ZERO_POINT_TURN_TYPES:
            points = 0
        if turn_type in ("pass", "exchange"):
            clean_word = None

        turn = Turn(index, turn_type, clean_word, points)
        self.turns.append(turn)
        return turn

    def undo_last_turn(self, player: object) -> bool:
        """Remove the player's latest move. ``False`` if they have none."""
        self._require_open()
        index = self._require_player(player)
        for position in range(len(self.turns) - 1, -1, -1):
            if self.turns[position].player == index:
                del self.turns[position]
                return True
        return False

    # -- scores ---------------------------------------------------------
    def running_score(self, player: int) -> int:
        """Points from moves only, without the closing adjustments."""
        return sum(t.points for t in self.turns if t.player == player)

    def final_score(self, player: int) -> int:
        """Running score minus the tile penalty plus the bonus."""
        p = self.players[player]
        return self.running_score(player) - p.penalty + p.bonus

    def score(self, player: int) -> int:
        """Final score once finished, running score before."""
        return self.final_score(player) if self.finished else self.running_score(player)

    def scrabble_count(self, player: int) -> int:
        return sum(
            1 for t in self.turns if t.player == player and t.turn_type == "scrabble"
        )

    def move_count(self, player: int) -> int:
        return sum(1 for t in self.turns if t.player == player)

    def average_score(self) -> float:
        """Average running score of all players."""
        total = sum(self.running_score(i) for i in range(len(self.players)))
        return round(total / len(self.players), 1)

    def ranking(self) -> list[tuple[int, int]]:
        """``(player_index, score)`` pairs, best first; ties keep turn order."""
        scored = [(i, self.score(i)) for i in range(len(self.players))]
        return sorted(scored, key=lambda pair: pair[1], reverse=True)

    # -- closing --------------------------------------------------------
    def finish(self, remaining: Sequence[str]) -> None:
        """Apply the closing rule; ``remaining[i]`` are player i's tiles."""
        self._require_open()
        racks = {
            i: ((remaining[i] if i < len(remaining) else "") or "")
            for i in range(len(self.players))
        }
        if any(len(rack.strip()) > MAX_RACK_LENGTH for rack in racks.values()):
            raise DomainError(
                f"Remaining tiles are limited to {MAX_RACK_LENGTH} characters."
            )
        adjustments = compute_closing(racks, self.language)
        for index, player in enumerate(self.players):
            adjustment = adjustments[index]
            player.remaining_tiles = adjustment.remaining_tiles
            player.penalty = adjustment.penalty
            player.bonus = adjustment.bonus
        self.finished = True


def new_game(raw_names: str, language: str) -> Game:
    """Create a game from the comma-separated names typed by the user."""
    return Game(language, parse_player_names(raw_names))
