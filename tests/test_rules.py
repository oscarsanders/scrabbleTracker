"""rules.py: closing rule, RF-13 and RF-14."""

from scrabble_tracker.rules import compute_closing


def test_single_finisher_gets_bonus_and_others_pay():
    result = compute_closing({1: "", 2: "AE"}, "es")
    assert result[1].bonus == 2 and result[1].penalty == 0
    assert result[1].emptied_rack is True
    assert result[2].penalty == 2 and result[2].bonus == 0


def test_bonus_sums_all_other_racks():
    result = compute_closing({1: "", 2: "AE", 3: "Z"}, "es")
    assert result[1].bonus == 2 + 10


def test_nobody_finished_only_penalties():
    result = compute_closing({1: "AE", 2: "Z"}, "es")
    assert all(r.bonus == 0 for r in result.values())
    assert result[1].penalty == 2 and result[2].penalty == 10


def test_two_finishers_no_bonus():
    result = compute_closing({1: "", 2: "", 3: "Z"}, "es")
    assert all(r.bonus == 0 for r in result.values())
    assert result[3].penalty == 10


def test_solo_player_emptying_rack_has_no_bonus():
    result = compute_closing({1: ""}, "es")
    assert result[1].bonus == 0 and result[1].penalty == 0


def test_whitespace_counts_as_empty_and_none_is_tolerated():
    result = compute_closing({1: "   ", 2: "A"}, "en")
    assert result[1].emptied_rack and result[1].bonus == 1
