"""Gradio application: layout and event wiring.

Design notes (see ``docs/adr/0002-gradio-ui-framework.md``):

* This module deliberately does NOT use ``from __future__ import
  annotations``: Gradio injects the HTTP request into handlers by
  inspecting the real ``request: gr.Request`` annotation object.
* Handlers stay thin. They authenticate the request, open one
  transaction, call a service, and describe which components to update.
  Business rules live in ``scrabble_tracker.services``.
* Handlers return ``{component: value}`` dictionaries. Gradio only
  updates the listed components, and returning by name avoids the
  positional mismatches of long output tuples.
* The acting user always comes from the server-side ``request.username``
  (set by Gradio after the login form), never from a browser-supplied
  field, and every game access is re-authorised in the service layer.
"""

import logging
from collections.abc import Callable
from typing import Any

import gradio as gr
from sqlalchemy.orm import Session, sessionmaker

from scrabble_tracker.db import session_scope
from scrabble_tracker.errors import DomainError
from scrabble_tracker.models import Game, User
from scrabble_tracker.services import accounts, games
from scrabble_tracker.tiles import LANGUAGE_LABELS
from scrabble_tracker.ui import render
from scrabble_tracker.ui.labels import MODE_LABELS, TURN_TYPE_LABELS
from scrabble_tracker.views import (
    build_active_games,
    build_game_view,
    build_history,
    build_profile,
    build_user_rows,
)

logger = logging.getLogger("scrabble_tracker.ui")

RACK_SLOTS = 4  # one "tiles left" box per possible player
if RACK_SLOTS != games.MAX_PLAYERS:  # pragma: no cover - guards future edits
    raise RuntimeError("RACK_SLOTS must equal games.MAX_PLAYERS (on_finish signature).")


def _to_int(value: Any, *, field: str = "Value") -> int | None:
    """Coerce a Gradio input (int, float, str or None) to ``int | None``."""
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise DomainError(f"{field} must be a number.") from None
    if not number.is_integer():
        raise DomainError(f"{field} must be a whole number.")
    return int(number)


def build_demo(session_factory: sessionmaker[Session]) -> gr.Blocks:
    """Build the Gradio Blocks app.

    Authentication is configured at launch time (``launch(auth=...)``),
    so every handler can rely on ``request.username`` being set.
    """
    components: dict[str, Any] = {}

    def out(values: dict[str, Any]) -> dict[Any, Any]:
        """Translate ``{name: value}`` into ``{component: value}``."""
        return {components[name]: value for name, value in values.items()}

    def run(
        request: gr.Request,
        work: Callable[[Session, User], dict[str, Any]],
        error_key: str,
    ) -> dict[Any, Any]:
        """Authenticate, run ``work`` in one transaction, handle errors.

        Expected failures (:class:`DomainError`) are shown next to the
        form identified by ``error_key``; anything else is logged and
        surfaced as a generic error without internal details.
        """
        try:
            with session_scope(session_factory) as session:
                username = getattr(request, "username", None)
                user = accounts.require_user(session, username)
                return out(work(session, user))
        except DomainError as exc:
            return out({error_key: render.message_html("error", str(exc))})
        except Exception:
            logger.exception("unhandled_ui_error")
            raise gr.Error("Something went wrong. Please try again.") from None

    # ------------------------------------------------------------------
    # Component update builders
    # ------------------------------------------------------------------
    def play_updates(
        game: Game, *, selected: int | None = None, with_racks: bool = False
    ) -> dict[str, Any]:
        view = build_game_view(game)
        ids = [player_id for player_id, _ in view.roster]
        current = selected if selected in ids else (ids[0] if ids else None)
        updates: dict[str, Any] = {
            "game_id": game.id,
            "play_board": (
                render.ranking_html(view)
                if view.is_finished
                else render.scoreboard_html(view)
            ),
            "play_log": render.turn_log_html(view),
            "turn_player": gr.Dropdown(
                choices=[(name, pid) for pid, name in view.roster], value=current
            ),
        }
        if with_racks or view.is_finished:
            for slot in range(RACK_SLOTS):
                key = f"rack{slot}"
                if slot < len(view.roster) and not view.is_finished:
                    name = view.roster[slot][1]
                    updates[key] = gr.Textbox(
                        label=f"{name} — tiles left (empty if none)",
                        visible=True,
                        value="",
                    )
                else:
                    updates[key] = gr.Textbox(visible=False, value="")
        return updates

    def home_updates(session: Session, user: User) -> dict[str, Any]:
        active = build_active_games(games.list_active_games(session, user))
        history = build_history(user)
        users = accounts.list_users(session, actor=user) if user.is_admin else []
        return {
            "header": render.header_html(user.username, user.is_admin),
            "home_active": gr.Dropdown(
                choices=[(g.label, g.game_id) for g in active], value=None
            ),
            "home_recent": render.history_html(
                history[:5], empty="No finished games yet."
            ),
            "history_html": render.history_html(history),
            "history_select": gr.Dropdown(
                choices=[(f"Game #{r.game_id} · {r.date}", r.game_id) for r in history],
                value=None,
            ),
            "profile_html": render.profile_html(build_profile(user)),
            "admin_panel": gr.Column(visible=user.is_admin),
            "admin_notice": (
                ""
                if user.is_admin
                else render.message_html(
                    "info", "Only administrators can manage accounts."
                )
            ),
            "users_html": (
                render.users_html(build_user_rows(users)) if user.is_admin else ""
            ),
            "delete_user": gr.Dropdown(
                choices=[(u.username, u.id) for u in users if not u.is_admin],
                value=None,
            ),
        }

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    with gr.Blocks(title="Scrabble Tracker") as demo:
        components["game_id"] = gr.State(None)
        components["header"] = gr.HTML("")
        gr.Button("Log out", link="/logout", size="sm")

        with gr.Tabs() as tabs:
            components["tabs"] = tabs

            with gr.Tab("Home", id="home") as tab_home:
                components["home_active"] = gr.Dropdown(
                    label="Games in progress", choices=[], value=None
                )
                resume_btn = gr.Button("Resume selected game", variant="primary")
                components["home_msg"] = gr.HTML("")
                gr.Markdown("### Recent games")
                components["home_recent"] = gr.HTML("")

            with gr.Tab("New game", id="new"):
                new_mode = gr.Radio(
                    label="Mode",
                    choices=[(label, code) for code, label in MODE_LABELS.items()],
                    value="multiplayer",
                )
                new_language = gr.Radio(
                    label="Tile language",
                    choices=[(label, code) for code, label in LANGUAGE_LABELS.items()],
                    value="es",
                )
                new_players = gr.Textbox(
                    label="Other players (comma-separated)",
                    placeholder="Ana, Luis",
                    info=(
                        "You are added automatically. Registered usernames are "
                        "linked to their accounts; other names play as guests. "
                        "Ignored in solo mode."
                    ),
                )
                start_btn = gr.Button("Start game", variant="primary")
                components["new_msg"] = gr.HTML("")

            with gr.Tab("Play", id="play"):
                components["play_board"] = gr.HTML(
                    render.message_html("info", "Start or resume a game first.")
                )
                refresh_btn = gr.Button("Refresh", size="sm")
                gr.Markdown("### Record a move")
                components["turn_player"] = gr.Dropdown(
                    label="Player", choices=[], value=None
                )
                components["turn_type"] = turn_type = gr.Dropdown(
                    label="Move type",
                    choices=[(TURN_TYPE_LABELS[t], t) for t in TURN_TYPE_LABELS],
                    value="normal",
                )
                components["turn_word"] = gr.Textbox(
                    label="Word", placeholder="e.g. QUIJOTE"
                )
                components["turn_points"] = gr.Number(
                    label="Points (ignored for foul, pass and exchange)",
                    value=0,
                    precision=0,
                    minimum=0,
                )
                with gr.Row():
                    add_btn = gr.Button("Add move", variant="primary")
                    undo_btn = gr.Button("Undo player's last move")
                components["play_msg"] = gr.HTML("")
                components["play_log"] = gr.HTML("")
                with gr.Accordion("Finish game", open=False):
                    gr.Markdown(
                        "Enter the tiles each player still holds. Leave a field "
                        "**empty** for the player who used all their tiles: they "
                        "gain the value of everyone else's tiles."
                    )
                    rack_boxes = []
                    for slot in range(RACK_SLOTS):
                        box = gr.Textbox(label=f"Player {slot + 1}", visible=False)
                        components[f"rack{slot}"] = box
                        rack_boxes.append(box)
                    finish_btn = gr.Button(
                        "Close game and show ranking", variant="stop"
                    )

            with gr.Tab("History", id="history") as tab_history:
                components["history_html"] = gr.HTML("")
                components["history_select"] = gr.Dropdown(
                    label="Open a finished game", choices=[], value=None
                )
                view_btn = gr.Button("View ranking")
                components["history_detail"] = gr.HTML("")

            with gr.Tab("Profile", id="profile") as tab_profile:
                components["profile_html"] = gr.HTML("")
                with gr.Accordion("Change password", open=False):
                    components["pw_current"] = gr.Textbox(
                        label="Current password", type="password"
                    )
                    components["pw_new"] = gr.Textbox(
                        label="New password", type="password"
                    )
                    components["pw_confirm"] = gr.Textbox(
                        label="Repeat new password", type="password"
                    )
                    pw_btn = gr.Button("Update password")
                    components["pw_msg"] = gr.HTML("")

            with gr.Tab("Admin", id="admin") as tab_admin:
                components["admin_notice"] = gr.HTML("")
                with gr.Column(visible=False) as admin_panel:
                    components["admin_panel"] = admin_panel
                    components["users_html"] = gr.HTML("")
                    gr.Markdown("### Add a player account")
                    components["new_user_name"] = gr.Textbox(label="Username")
                    components["new_user_pw"] = gr.Textbox(
                        label="Initial password", type="password"
                    )
                    create_user_btn = gr.Button("Create account", variant="primary")
                    gr.Markdown("### Remove an account")
                    components["delete_user"] = gr.Dropdown(
                        label="Account", choices=[], value=None
                    )
                    delete_user_btn = gr.Button("Delete account", variant="stop")
                    components["admin_msg"] = gr.HTML("")

        all_outputs = list(components.values())

        # --------------------------------------------------------------
        # Handlers
        # --------------------------------------------------------------
        def on_refresh_home(request: gr.Request):
            return run(request, home_updates, "home_msg")

        def on_resume(game_id_value, request: gr.Request):
            def work(session: Session, user: User) -> dict[str, Any]:
                chosen = _to_int(game_id_value, field="Game")
                if chosen is None:
                    raise DomainError("Select a game first.")
                game = games.get_game_for_user(session, chosen, user)
                updates = play_updates(game, with_racks=True)
                updates.update({"tabs": gr.Tabs(selected="play"), "play_msg": ""})
                return updates

            return run(request, work, "home_msg")

        def on_start(mode, language, others, request: gr.Request):
            def work(session: Session, user: User) -> dict[str, Any]:
                game = games.start_game(
                    session,
                    creator=user,
                    mode=mode,
                    language=language,
                    other_players=others or "",
                )
                updates = play_updates(game, with_racks=True)
                updates.update(
                    {
                        "tabs": gr.Tabs(selected="play"),
                        "new_msg": "",
                        "turn_word": "",
                        "turn_points": 0,
                        "play_msg": render.message_html(
                            "ok", f"Game #{game.id} started."
                        ),
                    }
                )
                return updates

            return run(request, work, "new_msg")

        def on_refresh_play(current_game, player, request: gr.Request):
            def work(session: Session, user: User) -> dict[str, Any]:
                game = games.get_game_for_user(session, current_game, user)
                return play_updates(game, selected=_to_int(player))

            return run(request, work, "play_msg")

        def on_add_turn(
            current_game, player, move_type, word, points, request: gr.Request
        ):
            def work(session: Session, user: User) -> dict[str, Any]:
                game = games.get_game_for_user(session, current_game, user)
                player_id = _to_int(player, field="Player")
                games.add_turn(
                    session,
                    game=game,
                    player_id=player_id,
                    turn_type=move_type,
                    word=word,
                    points=_to_int(points, field="Points") or 0,
                )
                updates = play_updates(game, selected=player_id)
                updates.update(
                    {
                        "turn_word": "",
                        "turn_points": 0,
                        "play_msg": render.message_html("ok", "Move recorded."),
                    }
                )
                return updates

            return run(request, work, "play_msg")

        def on_undo(current_game, player, request: gr.Request):
            def work(session: Session, user: User) -> dict[str, Any]:
                game = games.get_game_for_user(session, current_game, user)
                player_id = _to_int(player, field="Player")
                removed = games.undo_last_turn(session, game=game, player_id=player_id)
                updates = play_updates(game, selected=player_id)
                updates["play_msg"] = (
                    render.message_html("ok", "Last move removed.")
                    if removed
                    else render.message_html("info", "That player has no moves yet.")
                )
                return updates

            return run(request, work, "play_msg")

        # One explicit parameter per rack box: Gradio only injects
        # ``request`` into functions with a named ``gr.Request`` parameter.
        def on_finish(current_game, rack0, rack1, rack2, rack3, request: gr.Request):
            racks = [rack0, rack1, rack2, rack3]

            def work(session: Session, user: User) -> dict[str, Any]:
                game = games.get_game_for_user(session, current_game, user)
                roster_ids = [player.id for player in game.players]
                remaining = {
                    pid: (racks[slot] or "") for slot, pid in enumerate(roster_ids)
                }
                games.finish_game(session, game=game, remaining_by_player=remaining)
                updates = play_updates(game)
                updates["play_msg"] = render.message_html(
                    "ok", "Game finished. Final ranking below."
                )
                return updates

            return run(request, work, "play_msg")

        def on_view_history(game_id_value, request: gr.Request):
            def work(session: Session, user: User) -> dict[str, Any]:
                chosen = _to_int(game_id_value, field="Game")
                if chosen is None:
                    raise DomainError("Select a finished game first.")
                view = build_game_view(games.get_game_for_user(session, chosen, user))
                return {
                    "history_detail": (
                        render.ranking_html(view)
                        if view.is_finished
                        else render.scoreboard_html(view)
                    )
                }

            return run(request, work, "history_detail")

        def on_change_password(current, new, confirm, request: gr.Request):
            def work(session: Session, user: User) -> dict[str, Any]:
                if (new or "") != (confirm or ""):
                    raise DomainError("The new passwords do not match.")
                accounts.change_password(session, user, current or "", new or "")
                return {
                    "pw_msg": render.message_html("ok", "Password updated."),
                    "pw_current": "",
                    "pw_new": "",
                    "pw_confirm": "",
                }

            return run(request, work, "pw_msg")

        def on_create_user(name, password, request: gr.Request):
            def work(session: Session, user: User) -> dict[str, Any]:
                created = accounts.create_user_as_admin(
                    session, actor=user, username=name or "", password=password or ""
                )
                updates = home_updates(session, user)
                updates.update(
                    {
                        "admin_msg": render.message_html(
                            "ok", f"Account '{created.username}' created."
                        ),
                        "new_user_name": "",
                        "new_user_pw": "",
                    }
                )
                return updates

            return run(request, work, "admin_msg")

        def on_delete_user(user_id_value, request: gr.Request):
            def work(session: Session, user: User) -> dict[str, Any]:
                target_id = _to_int(user_id_value, field="Account")
                if target_id is None:
                    raise DomainError("Select an account first.")
                removed = accounts.delete_user(session, actor=user, user_id=target_id)
                updates = home_updates(session, user)
                updates["admin_msg"] = render.message_html(
                    "ok", f"Account '{removed.username}' deleted."
                )
                return updates

            return run(request, work, "admin_msg")

        # --------------------------------------------------------------
        # Event wiring
        # --------------------------------------------------------------
        game_state = components["game_id"]
        turn_player = components["turn_player"]

        demo.load(on_refresh_home, None, all_outputs)
        for tab in (tab_home, tab_history, tab_profile, tab_admin):
            tab.select(on_refresh_home, None, all_outputs)

        resume_btn.click(on_resume, [components["home_active"]], all_outputs)
        start_btn.click(on_start, [new_mode, new_language, new_players], all_outputs)
        refresh_btn.click(on_refresh_play, [game_state, turn_player], all_outputs)
        add_btn.click(
            on_add_turn,
            [
                game_state,
                turn_player,
                turn_type,
                components["turn_word"],
                components["turn_points"],
            ],
            all_outputs,
        )
        undo_btn.click(on_undo, [game_state, turn_player], all_outputs)
        finish_btn.click(on_finish, [game_state, *rack_boxes], all_outputs)
        view_btn.click(on_view_history, [components["history_select"]], all_outputs)
        pw_btn.click(
            on_change_password,
            [
                components["pw_current"],
                components["pw_new"],
                components["pw_confirm"],
            ],
            all_outputs,
        )
        create_user_btn.click(
            on_create_user,
            [components["new_user_name"], components["new_user_pw"]],
            all_outputs,
        )
        delete_user_btn.click(
            on_delete_user, [components["delete_user"]], all_outputs
        )

    return demo
