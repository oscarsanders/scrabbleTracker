"""Human-readable labels for domain codes shown in the UI."""

from __future__ import annotations

TURN_TYPE_LABELS: dict[str, str] = {
    "normal": "Word",
    "scrabble": "Scrabble (all 7 tiles)",
    "foul": "Foul (invalid word)",
    "pass": "Pass",
    "exchange": "Exchange tiles",
}
