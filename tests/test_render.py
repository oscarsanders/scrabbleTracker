"""ui/render.py: user text must always be escaped (RNF-04)."""

from scrabble_tracker.game import Game
from scrabble_tracker.ui import render

XSS = '<img src=x onerror="alert(1)">'


def _game(finished=False):
    g = Game("es", [XSS, "Bo"])
    g.add_turn(0, "scrabble", XSS, 50)
    g.add_turn(1, "normal", "SOL", 10)
    if finished:
        g.finish(["Z", ""])
    return g


def test_scoreboard_escapes_names_and_shows_scores():
    html = render.scoreboard_html(_game())
    assert "<img" not in html and "&lt;img" in html
    assert "50" in html and "Game in progress" in html


def test_turn_log_escapes_word_and_player_and_is_newest_first():
    html = render.turn_log_html(_game())
    assert "<img" not in html
    assert html.count("&lt;img") == 2
    assert html.index("SOL") < html.index("&lt;img")


def test_turn_log_empty_state():
    assert "No moves yet" in render.turn_log_html(Game("es", ["Ana"]))


def test_ranking_shows_adjustments_and_places():
    html = render.ranking_html(_game(finished=True))
    assert "1." in html and "2." in html
    assert "−10 remaining tiles" in html and "+10 went out first" in html
    assert "<img" not in html


def test_message_html_escapes_and_clears():
    assert render.message_html("ok", "") == ""
    assert "&lt;b&gt;" in render.message_html("error", "<b>x</b>")
    assert "st-msg-info" in render.message_html("weird-kind", "hi")


def test_header_is_static():
    assert "SCRABBLE" not in render.header_html()  # letters are separate tiles
    assert render.header_html().count("st-tile") == 8
