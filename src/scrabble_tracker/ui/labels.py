"""Human-readable labels for domain codes shown in the UI."""

from __future__ import annotations

TURN_TYPE_LABELS: dict[str, str] = {
    "normal": "Word",
    "scrabble": "Bingo (Scrabble)",
    "foul": "Foul (invalid word)",
    "pass": "Pass",
    "exchange": "Exchange tiles",
}
