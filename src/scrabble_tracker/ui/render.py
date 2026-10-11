"""Pure HTML renderers for the Gradio ``HTML`` components.

``gr.HTML`` does **not** sanitise its content, and every name, word and
username shown here is user-controlled. All dynamic text therefore goes
through :func:`esc`. The CSS classes used here are defined in
``theme.CSS``.
"""

from __future__ import annotations

import html
from collections.abc import Sequence

from scrabble_tracker.tiles import LANGUAGE_LABELS
from scrabble_tracker.ui.labels import MODE_LABELS, TURN_TYPE_LABELS
from scrabble_tracker.views import (
    GameView,
    HistoryRow,
    ProfileView,
    UserRow,
)

_MESSAGE_KINDS = ("ok", "error", "info")


def esc(value: object) -> str:
    """HTML-escape any value (quotes included)."""
    return html.escape(str(value), quote=True)


def message_html(kind: str, text: str) -> str:
    """A feedback banner; an empty ``text`` clears it."""
    if not text:
        return ""
    css = kind if kind in _MESSAGE_KINDS else "info"
    return f'<div class="st-msg st-msg-{css}" role="status">{esc(text)}</div>'


def header_html(username: str, is_admin: bool) -> str:
    tiles = "".join(f'<span class="st-tile">{esc(c)}</span>' for c in "SCRABBLE")
    badge = '<span class="st-badge st-badge-admin">admin</span>' if is_admin else ""
    return (
        '<div class="st-header">'
        f'<div class="st-brand" aria-label="Scrabble Tracker">{tiles}</div>'
        f'<div class="st-user">Signed in as <strong>{esc(username)}</strong> '
        f"{badge}</div>"
        "</div>"
    )


def _meta(view: GameView) -> str:
    mode = MODE_LABELS.get(view.mode, view.mode)
    language = LANGUAGE_LABELS.get(view.language, view.language)
    return (
        f"{esc(mode)} · Tiles: {esc(language)} · "
        f"Game average: {esc(view.average_score)}"
    )


def scoreboard_html(view: GameView) -> str:
    """Live scoreboard for a game in progress (RF-09, RF-10)."""
    rows = []
    for index, player in enumerate(view.ranking):
        leader = " st-leader" if index == 0 and len(view.ranking) > 1 else ""
        rows.append(
            f'<div class="st-player{leader}">'
            f'<div><strong>{esc(player.name)}</strong>'
            f'<div class="st-muted">{esc(player.scrabbles)} bingo(s) · '
            f"{esc(player.turns)} moves</div></div>"
            f'<span class="st-score">{esc(player.score)}</span></div>'
        )
    return (
        '<div class="st-card">'
        f"<h3>Game #{esc(view.game_id)}</h3>"
        f'<p class="st-muted">{_meta(view)}</p>' + "".join(rows) + "</div>"
    )


def ranking_html(view: GameView) -> str:
    """Final standings of a finished game (RF-15)."""
    rows = []
    for position, player in enumerate(view.ranking, start=1):
        adjustments = []
        if player.penalty:
            adjustments.append(f"−{esc(player.penalty)} remaining tiles")
        if player.bonus:
            adjustments.append(f"+{esc(player.bonus)} went out first")
        detail = " · ".join(adjustments) or "no adjustments"
        leader = " st-leader" if position == 1 else ""
        rows.append(
            f'<div class="st-player{leader}">'
            f"<div><strong>{position}. {esc(player.name)}</strong>"
            f'<div class="st-muted">{detail} · {esc(player.scrabbles)} bingo(s)</div>'
            f'</div><span class="st-score">{esc(player.score)}</span></div>'
        )
    return (
        '<div class="st-card">'
        f"<h3>Game #{esc(view.game_id)} — final ranking</h3>"
        f'<p class="st-muted">{_meta(view)}</p>' + "".join(rows) + "</div>"
    )


def turn_log_html(view: GameView) -> str:
    """Moves recorded so far, newest first (RF-07)."""
    if not view.turns:
        return '<div class="st-card"><p class="st-muted">No moves yet.</p></div>'
    body = "".join(
        "<tr>"
        f"<td>{esc(t.player)}</td>"
        f'<td><span class="st-badge st-badge-{esc(t.turn_type)}">'
        f"{esc(TURN_TYPE_LABELS.get(t.turn_type, t.turn_type))}</span></td>"
        f"<td>{esc(t.word) if t.word else '—'}</td>"
        f"<td>{esc(t.points)}</td></tr>"
        for t in view.turns
    )
    return (
        '<div class="st-card"><h3>Moves</h3><div class="st-table-wrap"><table>'
        "<tr><th>Player</th><th>Type</th><th>Word</th><th>Points</th></tr>"
        f"{body}</table></div></div>"
    )


def history_html(
    rows: Sequence[HistoryRow], *, empty: str = "No finished games."
) -> str:
    """Finished games of the current user (RF-04)."""
    if not rows:
        return f'<div class="st-card"><p class="st-muted">{esc(empty)}</p></div>'
    body = "".join(
        "<tr>"
        f"<td>#{esc(r.game_id)}</td><td>{esc(r.date)}</td>"
        f"<td>{esc(MODE_LABELS.get(r.mode, r.mode))}</td>"
        f"<td>{esc(r.language.upper())}</td>"
        f"<td>{esc(r.final_score)}</td>"
        f"<td>{esc(r.position)}/{esc(r.players)}</td></tr>"
        for r in rows
    )
    return (
        '<div class="st-card"><div class="st-table-wrap"><table>'
        "<tr><th>Game</th><th>Date</th><th>Mode</th><th>Lang</th>"
        "<th>Score</th><th>Place</th></tr>"
        f"{body}</table></div></div>"
    )


def profile_html(profile: ProfileView) -> str:
    """Personal statistics (RF-03)."""
    stats = (
        ("Games played", profile.total_games),
        ("Average score", profile.average_score),
        ("Best score", profile.best_score),
        ("Bingos", profile.total_scrabbles),
        ("Wins", profile.wins),
    )
    cells = "".join(
        f'<div class="st-stat"><span class="st-stat-value">{esc(value)}</span>'
        f'<span class="st-muted">{esc(label)}</span></div>'
        for label, value in stats
    )
    return (
        '<div class="st-card">'
        f"<h3>{esc(profile.username)}</h3>"
        f'<div class="st-stats">{cells}</div></div>'
    )


def users_html(rows: Sequence[UserRow]) -> str:
    """Account list for administrators (RF-05)."""
    body = "".join(
        "<tr>"
        f"<td>{esc(r.username)}</td>"
        f"<td>{'admin' if r.is_admin else 'player'}</td>"
        f"<td>{esc(r.created)}</td></tr>"
        for r in rows
    )
    return (
        '<div class="st-card"><div class="st-table-wrap"><table>'
        "<tr><th>User</th><th>Role</th><th>Created</th></tr>"
        f"{body}</table></div></div>"
    )
