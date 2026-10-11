"""Gradio application: one game per browser session, kept only in memory.

Design notes (see ``docs/adr/0005-stateless-single-game.md``):

* The ``Game`` lives in a per-session ``gr.State``. There is no database,
  no file and no module-level state, so visitors can never see each
  other's games, and closing the tab discards the game.
* Handlers are thin: they call the domain, ask ``presenter`` what to show
  and return ``{component: value}`` dictionaries (Gradio only updates the
  listed components, and naming them avoids positional mix-ups).
* Business rules live in ``scrabble_tracker.game``; HTML is built in
  ``ui.render`` with every dynamic value escaped.
"""

from typing import Any

import gradio as gr

from scrabble_tracker.errors import DomainError
from scrabble_tracker.game import Game, new_game
from scrabble_tracker.tiles import LANGUAGE_LABELS
from scrabble_tracker.ui import presenter, render
from scrabble_tracker.ui.labels import TURN_TYPE_LABELS
from scrabble_tracker.ui.presenter import RACK_SLOTS


def _to_int(value: Any, *, field: str) -> int | None:
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


def build_demo() -> gr.Blocks:
    """Build the Gradio Blocks app."""
    with gr.Blocks(title="Scrabble Tracker") as demo:
        game_state = gr.State(None)
        gr.HTML(render.header_html())

        # -- Setup screen ------------------------------------------------
        with gr.Column(visible=True) as setup_col:
            gr.Markdown("### New game")
            players_box = gr.Textbox(
                label="Players (comma-separated, 1 to 4)",
                placeholder="Ana, Luis",
                info="One name means a solo game.",
            )
            language = gr.Radio(
                label="Tile language",
                choices=[(label, code) for code, label in LANGUAGE_LABELS.items()],
                value="es",
            )
            start_btn = gr.Button("Start game", variant="primary")
            setup_msg = gr.HTML("")

        # -- Play screen -------------------------------------------------
        with gr.Column(visible=False) as play_col:
            board = gr.HTML("")
            gr.Markdown("### Record a move")
            player_dd = gr.Dropdown(label="Player", choices=[], value=None)
            type_dd = gr.Dropdown(
                label="Move type",
                choices=[(label, code) for code, label in TURN_TYPE_LABELS.items()],
                value="normal",
            )
            word_box = gr.Textbox(label="Word", placeholder="e.g. QUIJOTE")
            points_num = gr.Number(
                label="Points (ignored for foul, pass and exchange)",
                value=0,
                precision=0,
                minimum=0,
            )
            with gr.Row():
                add_btn = gr.Button("Add move", variant="primary")
                undo_btn = gr.Button("Undo player's last move")
            play_msg = gr.HTML("")
            log = gr.HTML("")
            with gr.Accordion("Finish game", open=False):
                gr.Markdown(
                    "Enter the tiles each player still holds. Leave a field "
                    "**empty** for the player who used all their tiles: they "
                    "gain the value of everyone else's tiles."
                )
                rack_boxes = [
                    gr.Textbox(label=f"Player {slot + 1}", visible=False)
                    for slot in range(RACK_SLOTS)
                ]
                finish_btn = gr.Button("Close game and show ranking", variant="stop")
            new_btn = gr.Button("Start a new game")

        all_outputs = [
            game_state,
            setup_col,
            play_col,
            setup_msg,
            board,
            log,
            player_dd,
            play_msg,
            word_box,
            points_num,
            *rack_boxes,
        ]

        # -- Update builders --------------------------------------------
        def panel_updates(
            game: Game, selected: int | None = None, message: str = ""
        ) -> dict[Any, Any]:
            panel = presenter.build_panel(game, selected)
            updates: dict[Any, Any] = {
                game_state: game,
                board: panel.board_html,
                log: panel.log_html,
                player_dd: gr.Dropdown(
                    choices=list(panel.roster), value=panel.selected
                ),
                play_msg: message,
            }
            for slot, box in enumerate(rack_boxes):
                label = panel.rack_labels[slot]
                updates[box] = gr.Textbox(
                    label=label or f"Player {slot + 1}",
                    visible=label is not None,
                    value="",
                )
            return updates

        def no_game() -> dict[Any, Any]:
            """Shown when a handler runs without a game (e.g. server restart)."""
            return {
                game_state: None,
                setup_col: gr.Column(visible=True),
                play_col: gr.Column(visible=False),
                setup_msg: render.message_html(
                    "info", "No game in progress. Start a new one."
                ),
            }

        # -- Handlers ----------------------------------------------------
        def on_start(names, tile_language):
            try:
                game = new_game(names or "", tile_language)
            except DomainError as exc:
                return {setup_msg: render.message_html("error", str(exc))}
            updates = panel_updates(
                game, message=render.message_html("ok", "Game started. Good luck!")
            )
            updates.update(
                {
                    setup_col: gr.Column(visible=False),
                    play_col: gr.Column(visible=True),
                    setup_msg: "",
                    word_box: "",
                    points_num: 0,
                }
            )
            return updates

        def on_add(game, player, move_type, word, points):
            if game is None:
                return no_game()
            try:
                index = _to_int(player, field="Player")
                points_value = _to_int(points, field="Points") or 0
                game.add_turn(index, move_type, word, points_value)
            except DomainError as exc:
                return {play_msg: render.message_html("error", str(exc))}
            updates = panel_updates(
                game, index, render.message_html("ok", "Move recorded.")
            )
            updates.update({word_box: "", points_num: 0})
            return updates

        def on_undo(game, player):
            if game is None:
                return no_game()
            try:
                index = _to_int(player, field="Player")
                removed = game.undo_last_turn(index)
            except DomainError as exc:
                return {play_msg: render.message_html("error", str(exc))}
            message = (
                render.message_html("ok", "Last move removed.")
                if removed
                else render.message_html("info", "That player has no moves yet.")
            )
            return panel_updates(game, index, message)

        # One explicit parameter per rack box, matching RACK_SLOTS == 4.
        def on_finish(game, rack0, rack1, rack2, rack3):
            if game is None:
                return no_game()
            try:
                game.finish([rack0, rack1, rack2, rack3])
            except DomainError as exc:
                return {play_msg: render.message_html("error", str(exc))}
            return panel_updates(
                game,
                message=render.message_html(
                    "ok", "Game finished. Final ranking above."
                ),
            )

        def on_new():
            updates = no_game()
            updates[setup_msg] = ""
            return updates

        # -- Wiring ------------------------------------------------------
        start_btn.click(on_start, [players_box, language], all_outputs)
        players_box.submit(on_start, [players_box, language], all_outputs)
        add_btn.click(
            on_add, [game_state, player_dd, type_dd, word_box, points_num], all_outputs
        )
        undo_btn.click(on_undo, [game_state, player_dd], all_outputs)
        finish_btn.click(on_finish, [game_state, *rack_boxes], all_outputs)
        new_btn.click(on_new, None, all_outputs)

    return demo
