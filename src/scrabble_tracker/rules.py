"""End-of-game scoring rule as a pure function.

Extracted from the persistence-aware service so the rule that matters
most to players can be tested exhaustively without a database
(requirements RF-13 and RF-14).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from scrabble_tracker.tiles import rack_value


@dataclass(frozen=True)
class ClosingAdjustment:
    """Score adjustment applied to one player when a game is closed."""

    remaining_tiles: str
    penalty: int
    bonus: int
    emptied_rack: bool


def compute_closing(
    remaining_by_player: Mapping[int, str], language: str
) -> dict[int, ClosingAdjustment]:
    """Compute penalties and the bonus for a closing game.

    Rules:

    * Every player loses the value of their remaining tiles (RF-13).
    * If **exactly one** player emptied their rack (empty string), that
      player gains the combined value of everybody else's remaining
      tiles and suffers no penalty (RF-14).
    * If nobody, or more than one player, emptied their rack (for
      instance a game ended by consecutive passes) there is no bonus.

    Args:
        remaining_by_player: maps a player id to the string of tiles the
            player still holds; blank or whitespace means "none left".
        language: tile-value table to use (``"es"`` or ``"en"``).
    """
    racks = {pid: (rack or "").strip() for pid, rack in remaining_by_player.items()}
    penalties = {pid: rack_value(rack, language) for pid, rack in racks.items()}

    finishers = [pid for pid, rack in racks.items() if rack == ""]
    winner = finishers[0] if len(finishers) == 1 else None
    bonus = (
        sum(value for pid, value in penalties.items() if pid != winner)
        if winner is not None
        else 0
    )

    return {
        pid: ClosingAdjustment(
            remaining_tiles=rack,
            penalty=0 if pid == winner else penalties[pid],
            bonus=bonus if pid == winner else 0,
            emptied_rack=rack == "",
        )
        for pid, rack in racks.items()
    }
