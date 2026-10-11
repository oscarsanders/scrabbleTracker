"""game.py: the whole single-game domain (RF-01 .. RF-10)."""

import pytest

from scrabble_tracker.errors import DomainError
from scrabble_tracker.game import (
    MAX_RACK_LENGTH,
    MAX_TURNS,
    Game,
    new_game,
    parse_player_names,
)


def _duo():
    return Game("es", ["Ana", "Luis"])


def test_parse_player_names():
    assert parse_player_names(" Ana , ,Luis,, ") == ["Ana", "Luis"]
    assert parse_player_names("") == []
    assert parse_player_names(None) == []


def test_new_game_solo_and_multiplayer():
    assert [p.name for p in new_game("Ana", "es").players] == ["Ana"]
    assert [p.name for p in new_game("Ana, Luis, Eva", "en").players] == [
        "Ana",
        "Luis",
        "Eva",
    ]


@pytest.mark.parametrize(
    ("names", "language"),
    [
        ("", "es"),
        ("   ,  ", "es"),
        ("Ana", "fr"),
        ("Ana, ana", "es"),
        ("a, b, c, d, e", "es"),
        ("x" * 33, "es"),
    ],
)
def test_new_game_validation(names, language):
    with pytest.raises(DomainError):
        new_game(names, language)


def test_turns_and_running_scores():
    g = _duo()
    g.add_turn(0, "normal", "CASA", 20)
    g.add_turn(0, "normal", "SOL", 8)
    g.add_turn(1, "normal", "MESA", 10)
    assert (g.running_score(0), g.running_score(1)) == (28, 10)
    assert g.average_score() == 19.0
    assert g.ranking() == [(0, 28), (1, 10)]
    assert (g.move_count(0), g.move_count(1)) == (2, 1)


def test_ties_keep_turn_order():
    g = _duo()
    g.add_turn(0, "normal", "A", 5)
    g.add_turn(1, "normal", "B", 5)
    assert [i for i, _ in g.ranking()] == [0, 1]


def test_special_turns_force_zero_and_clean_words():
    g = Game("es", ["Ana"])
    foul = g.add_turn(0, "foul", "XYZ", 15)
    passed = g.add_turn(0, "pass", "ignored", 9)
    exchanged = g.add_turn(0, "exchange", "x", 3)
    plain = g.add_turn(0, "normal", "  hola  ", 4)
    assert (foul.points, foul.word) == (0, "XYZ")
    assert (passed.points, passed.word) == (0, None)
    assert (exchanged.points, exchanged.word) == (0, None)
    assert plain.word == "hola"
    assert g.add_turn(0, "normal", "   ", 1).word is None


def test_scrabble_counter():
    g = Game("es", ["Ana"])
    g.add_turn(0, "scrabble", "QUIJOTE", 68)
    g.add_turn(0, "normal", "SOL", 3)
    assert g.scrabble_count(0) == 1


@pytest.mark.parametrize(
    ("player", "turn_type", "points", "word"),
    [
        (0, "bonus", 5, "X"),
        (0, "normal", -1, "X"),
        (0, "normal", 1.5, "X"),
        (0, "normal", True, "X"),
        (0, "normal", 5, "W" * 65),
        (5, "normal", 5, "X"),
        (-1, "normal", 5, "X"),
        (None, "normal", 5, "X"),
        ("0", "normal", 5, "X"),
        (True, "normal", 5, "X"),
    ],
)
def test_add_turn_validation(player, turn_type, points, word):
    with pytest.raises(DomainError):
        Game("es", ["Ana"]).add_turn(player, turn_type, word, points)


def test_turn_limit_bounds_memory():
    g = Game("es", ["Ana"])
    for _ in range(MAX_TURNS):
        g.add_turn(0, "pass", None, 0)
    with pytest.raises(DomainError):
        g.add_turn(0, "pass", None, 0)


def test_undo_removes_only_that_players_latest_move():
    g = _duo()
    g.add_turn(0, "normal", "A", 10)
    g.add_turn(1, "normal", "B", 7)
    g.add_turn(0, "normal", "C", 4)
    assert g.undo_last_turn(0) is True
    assert (g.running_score(0), g.running_score(1)) == (10, 7)
    assert g.undo_last_turn(0) is True
    assert g.undo_last_turn(0) is False
    assert g.running_score(1) == 7


def test_finish_applies_penalty_and_bonus():
    g = _duo()
    g.add_turn(0, "normal", "CASA", 20)
    g.add_turn(1, "normal", "MESA", 15)
    g.finish(["", "AE"])
    assert g.finished
    assert (g.players[0].bonus, g.final_score(0)) == (2, 22)
    assert (g.players[1].penalty, g.final_score(1)) == (2, 13)
    assert g.players[1].remaining_tiles == "AE"
    assert g.ranking() == [(0, 22), (1, 13)]
    assert g.running_score(0) == 20  # moves-only score is unchanged


def test_finish_without_finisher_only_subtracts():
    g = _duo()
    g.add_turn(0, "normal", "CASA", 20)
    g.add_turn(1, "normal", "MESA", 15)
    g.finish(["AE", "Z"])
    assert (g.final_score(0), g.final_score(1)) == (18, 5)
    assert g.players[0].bonus == g.players[1].bonus == 0


def test_finish_can_reorder_ranking():
    g = _duo()
    g.add_turn(0, "normal", "A", 10)
    g.add_turn(1, "normal", "B", 9)
    g.finish(["Z", ""])  # Ana loses 10, Luis gains 10
    assert g.ranking() == [(1, 19), (0, 0)]


def test_finish_missing_racks_count_as_empty():
    g = _duo()
    g.finish([])
    assert g.finished and g.final_score(0) == 0


def test_finished_game_is_immutable():
    g = _duo()
    g.finish(["", ""])
    for call in (
        lambda: g.finish(["", ""]),
        lambda: g.add_turn(0, "normal", "A", 1),
        lambda: g.undo_last_turn(0),
    ):
        with pytest.raises(DomainError):
            call()


def test_rack_too_long_rejected_and_game_stays_open():
    g = _duo()
    with pytest.raises(DomainError):
        g.finish(["A" * (MAX_RACK_LENGTH + 1), ""])
    assert not g.finished and g.players[0].penalty == 0


def test_each_game_is_independent():
    a, b = Game("es", ["Ana"]), Game("es", ["Ana"])
    a.add_turn(0, "normal", "A", 10)
    assert b.running_score(0) == 0
