"""Tile values per language.

Pure functions with no dependency on the database or the UI, which makes
them trivial to test in isolation (SWEBOK KA05).

Known limitation: the Spanish table does not model the ``RR`` digraph
tile; see ``docs/RISKS.md``.
"""

from __future__ import annotations

TILE_VALUES: dict[str, dict[str, int]] = {
    "es": {
        "A": 1, "E": 1, "O": 1, "S": 1, "I": 1, "U": 1, "N": 1, "L": 1,
        "R": 1, "T": 1,
        "C": 3, "D": 2, "G": 2, "M": 3, "P": 3,
        "B": 3, "F": 4, "H": 4, "V": 4, "Y": 4,
        "CH": 5, "Q": 5,
        "J": 8, "LL": 8, "Ñ": 8, "X": 8,
        "Z": 10,
        "K": 10, "W": 10,
        "?": 0,  # blank tile
    },
    "en": {
        "A": 1, "E": 1, "I": 1, "O": 1, "U": 1, "L": 1, "N": 1, "S": 1,
        "T": 1, "R": 1,
        "D": 2, "G": 2,
        "B": 3, "C": 3, "M": 3, "P": 3,
        "F": 4, "H": 4, "V": 4, "W": 4, "Y": 4,
        "K": 5,
        "J": 8, "X": 8,
        "Q": 10, "Z": 10,
        "?": 0,  # blank tile
    },
}  # fmt: skip

SUPPORTED_LANGUAGES: tuple[str, ...] = tuple(TILE_VALUES)

LANGUAGE_LABELS: dict[str, str] = {
    "es": "Spanish",
    "en": "English",
}

_SPANISH_DIGRAPHS = ("CH", "LL")


def tile_value(letter: str, language: str) -> int:
    """Return the value of a single tile for ``language``.

    Unknown characters score 0 instead of raising, so that a typo while
    entering the remaining tiles cannot break the end-of-game flow.
    """
    table = TILE_VALUES.get(language, TILE_VALUES["en"])
    return table.get(letter.upper(), 0)


def rack_value(rack: str, language: str) -> int:
    """Return the total value of a string of remaining tiles.

    The Spanish digraphs ``CH`` and ``LL`` are recognised when written
    as such (so ``"CH"`` is one 5-point tile, not ``C`` + ``H``).
    Whitespace is ignored and unknown characters score 0.
    """
    rack = rack.strip().upper()
    if not rack:
        return 0
    table = TILE_VALUES.get(language, TILE_VALUES["en"])
    total = 0
    i = 0
    while i < len(rack):
        pair = rack[i : i + 2]
        if language == "es" and pair in _SPANISH_DIGRAPHS:
            total += table[pair]
            i += 2
            continue
        char = rack[i]
        if not char.isspace():
            total += table.get(char, 0)
        i += 1
    return total
