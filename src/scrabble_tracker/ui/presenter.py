"""Turns a :class:`Game` into plain display data (no Gradio imports).

Keeping this step pure means what the user will see — scoreboard,
move list, player choices and which boxes are visible — is unit-tested
without a browser.
"""

from __future__ import annotations

from dataclasses import dataclass

from scrabble_tracker.game import MAX_PLAYERS, Game
from scrabble_tracker.ui import render

#: One "tiles left" text box per possible player.
RACK_SLOTS = MAX_PLAYERS


@dataclass(frozen=True)
class PlayPanel:
    board_html: str
    log_html: str
    roster: tuple[tuple[str, int], ...]  # (player name, player index)
    selected: int | None
    rack_labels: tuple[str | None, ...]  # None = hide that box
    show_form: bool  # False once the game is finished


def build_panel(game: Game, selected: int | None = None) -> PlayPanel:
    """Describe the play screen for ``game``."""
    roster = tuple((p.name, i) for i, p in enumerate(game.players))
    valid = {index for _, index in roster}
    current = selected if selected in valid else (0 if roster else None)

    labels: list[str | None] = []
    for slot in range(RACK_SLOTS):
        if slot < len(game.players) and not game.finished:
            labels.append(f"{game.players[slot].name} — tiles left (empty if none)")
        else:
            labels.append(None)

    return PlayPanel(
        board_html=(
            render.ranking_html(game) if game.finished else render.scoreboard_html(game)
        ),
        log_html=render.turn_log_html(game),
        roster=roster,
        selected=current,
        rack_labels=tuple(labels),
        show_form=not game.finished,
    )
