"""Pure HTML renderers for the Gradio ``HTML`` components.

``gr.HTML`` does **not** sanitise its content and every player name and
word is user-controlled, so all dynamic text goes through :func:`esc`.
The CSS classes are defined in ``theme.CSS``.
"""

from __future__ import annotations

import html

from scrabble_tracker.game import Game
from scrabble_tracker.tiles import LANGUAGE_LABELS
from scrabble_tracker.ui.labels import TURN_TYPE_LABELS

_MESSAGE_KINDS = ("ok", "error", "info")


def esc(value: object) -> str:
    """HTML-escape any value (quotes included)."""
    return html.escape(str(value), quote=True)


def plural(count: int, noun: str) -> str:
    """``1 move`` / ``2 moves`` (regular English plurals only)."""
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def message_html(kind: str, text: str) -> str:
    """A feedback banner; an empty ``text`` clears it."""
    if not text:
        return ""
    css = kind if kind in _MESSAGE_KINDS else "info"
    return f'<div class="st-msg st-msg-{css}" role="status">{esc(text)}</div>'


def header_html() -> str:
    tiles = "".join(f'<span class="st-tile">{esc(c)}</span>' for c in "SCRABBLE")
    return (
        '<div class="st-header">'
        f'<div class="st-brand" aria-label="Scrabble Tracker">{tiles}</div>'
        '<div class="st-user">Score keeper</div></div>'
    )


def _meta(game: Game) -> str:
    language = LANGUAGE_LABELS.get(game.language, game.language)
    return (
        f"Tiles: {esc(language)} · "
        f"Game average: {esc(game.average_score())} per player"
    )


def _player_card(
    game: Game,
    index: int,
    score: int,
    *,
    prefix: str = "",
    badge: str = "",
    note: str = "",
    highlight: bool = False,
) -> str:
    """One player tile shared by the live board and the final ranking."""
    stats = (
        f"{plural(game.scrabble_count(index), 'scrabble')} · "
        f"{plural(game.move_count(index), 'move')} · "
        f"avg {esc(game.average_per_move(index))} per move"
    )
    css = " st-leader" if highlight else ""
    return (
        f'<div class="st-player{css}"><div>'
        f"<strong>{prefix}{esc(game.players[index].name)}</strong>{badge}"
        f'<div class="st-muted">{stats}</div>{note}</div>'
        f'<span class="st-score">{esc(score)}</span></div>'
    )


def scoreboard_html(game: Game) -> str:
    """Live scoreboard of a game in progress."""
    cards = "".join(
        _player_card(
            game, index, score, highlight=position == 1 and len(game.players) > 1
        )
        for position, index, score in game.standings()
    )
    return (
        '<div class="st-card"><h3>Game in progress</h3>'
        f'<p class="st-muted">{_meta(game)}</p>'
        f'<div class="st-players">{cards}</div></div>'
    )


def ranking_html(game: Game) -> str:
    """Final standings with a Winner badge (ties share it)."""
    winners = set(game.winners())
    label = "Winner (tie)" if len(winners) > 1 else "Winner"
    cards = []
    for position, index, score in game.standings():
        player = game.players[index]
        notes = []
        if player.penalty:
            notes.append(f"−{esc(player.penalty)} remaining tiles")
        if player.bonus:
            notes.append(f"+{esc(player.bonus)} went out first")
        is_winner = index in winners
        cards.append(
            _player_card(
                game,
                index,
                score,
                prefix=f"{position}. ",
                badge=(
                    f' <span class="st-badge st-badge-winner">🏆 {label}</span>'
                    if is_winner
                    else ""
                ),
                note=(
                    f'<div class="st-muted">{" · ".join(notes)}</div>' if notes else ""
                ),
                highlight=is_winner,
            )
        )
    return (
        '<div class="st-card"><h3>Final ranking</h3>'
        f'<p class="st-muted">{_meta(game)}</p>'
        f'<div class="st-players">{"".join(cards)}</div></div>'
    )


def turn_log_html(game: Game) -> str:
    """Moves recorded so far, newest first."""
    if not game.turns:
        return '<div class="st-card"><p class="st-muted">No moves yet.</p></div>'
    body = "".join(
        "<tr>"
        f"<td>{esc(game.players[t.player].name)}</td>"
        f'<td><span class="st-badge st-badge-{esc(t.turn_type)}">'
        f"{esc(TURN_TYPE_LABELS.get(t.turn_type, t.turn_type))}</span></td>"
        f"<td>{esc(t.word) if t.word else '—'}</td>"
        f"<td>{esc(t.points)}</td></tr>"
        for t in reversed(game.turns)
    )
    return (
        '<div class="st-card"><h3>Moves</h3><div class="st-table-wrap"><table>'
        "<tr><th>Player</th><th>Type</th><th>Word</th><th>Pts</th></tr>"
        f"{body}</table></div></div>"
    )
