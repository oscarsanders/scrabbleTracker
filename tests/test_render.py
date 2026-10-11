"""ui/render.py: user text must always be escaped (RNF-08)."""

from scrabble_tracker.ui import render
from scrabble_tracker.views import (
    GameView,
    HistoryRow,
    PlayerScore,
    ProfileView,
    TurnRow,
    UserRow,
)

XSS = '<img src=x onerror="alert(1)">'


def _view(finished=False):
    player = PlayerScore(1, XSS, 42, 1, 2, 3, 0, "")
    return GameView(
        game_id=7,
        mode="multiplayer",
        language="es",
        status="finished" if finished else "in_progress",
        average_score=21.0,
        ranking=(player, PlayerScore(2, "Bo", 10, 0, 1, 0, 3, "")),
        roster=((1, XSS), (2, "Bo")),
        turns=(TurnRow(XSS, "scrabble", XSS, 50),),
    )


def test_scoreboard_escapes_player_names():
    html = render.scoreboard_html(_view())
    assert "<img" not in html and "&lt;img" in html
    assert "42" in html and "Game #7" in html


def test_turn_log_escapes_word_and_player():
    html = render.turn_log_html(_view())
    assert "<img" not in html
    assert html.count("&lt;img") == 2


def test_turn_log_empty_state():
    empty = _view()
    empty = GameView(**{**empty.__dict__, "turns": ()})
    assert "No moves yet" in render.turn_log_html(empty)


def test_ranking_shows_adjustments_and_places():
    html = render.ranking_html(_view(finished=True))
    assert "1." in html and "2." in html
    assert "−3 remaining tiles" in html and "+3 went out first" in html


def test_message_html_escapes_and_clears():
    assert render.message_html("ok", "") == ""
    assert "&lt;b&gt;" in render.message_html("error", "<b>x</b>")
    assert "st-msg-info" in render.message_html("weird-kind", "hi")


def test_history_profile_users_header_escape():
    row = HistoryRow(3, "2026-10-01", "multiplayer", "es", 120, 1, 2)
    assert "#3" in render.history_html([row])
    assert "No finished games" in render.history_html([])
    profile = ProfileView(XSS, 1, 2.5, 99, 0, 1)
    assert "<img" not in render.profile_html(profile)
    assert "<img" not in render.users_html([UserRow(1, XSS, False, "2026-01-01")])
    assert "<img" not in render.header_html(XSS, True)
    assert "admin" in render.header_html("a", True)
