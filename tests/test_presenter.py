"""ui/presenter.py: what the play screen shows, without a browser."""

from scrabble_tracker.game import MAX_PLAYERS, Game
from scrabble_tracker.ui.presenter import RACK_SLOTS, build_panel


def test_rack_slots_match_player_limit():
    assert RACK_SLOTS == MAX_PLAYERS == 4


def test_roster_selection_and_hidden_racks():
    panel = build_panel(Game("es", ["Ana", "Luis"]))
    assert panel.roster == (("Ana", 0), ("Luis", 1))
    assert panel.selected == 0
    assert panel.rack_labels[0].startswith("Ana")
    assert panel.rack_labels[1].startswith("Luis")
    assert panel.rack_labels[2:] == (None, None)


def test_selected_player_is_kept_when_valid_else_first():
    game = Game("es", ["Ana", "Luis"])
    assert build_panel(game, 1).selected == 1
    assert build_panel(game, 9).selected == 0
    assert build_panel(game, None).selected == 0


def test_finished_game_shows_ranking_and_hides_racks():
    game = Game("es", ["Ana", "Luis"])
    game.finish(["", "A"])
    panel = build_panel(game)
    assert "Final ranking" in panel.board_html
    assert panel.rack_labels == (None,) * 4
    assert panel.show_form is False


def test_in_progress_shows_scoreboard():
    game = Game("es", ["Ana"])
    game.add_turn(0, "normal", "CASA", 12)
    panel = build_panel(game)
    assert "Game in progress" in panel.board_html and "12" in panel.board_html
    assert "CASA" in panel.log_html


def test_form_is_visible_while_game_is_open():
    assert build_panel(Game("es", ["Ana"])).show_form is True
