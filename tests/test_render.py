"""ui/render.py: escaping (RNF-04), wording and winner display."""

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


def test_plural():
    assert render.plural(0, "move") == "0 moves"
    assert render.plural(1, "scrabble") == "1 scrabble"
    assert render.plural(2, "scrabble") == "2 scrabbles"


def test_scoreboard_escapes_names_and_shows_scores():
    html = render.scoreboard_html(_game())
    assert "<img" not in html and "&lt;img" in html
    assert "50" in html and "Game in progress" in html


def test_scoreboard_uses_scrabble_wording_and_per_player_average():
    html = render.scoreboard_html(_game())
    assert "bingo" not in html.lower()
    assert "1 scrabble · 1 move · avg 50.0 per move" in html
    assert "0 scrabbles" in html  # Bo has none
    assert "Game average: 30.0 per player" in html


def test_new_game_scoreboard_shows_zeroes():
    html = render.scoreboard_html(Game("es", ["Ana", "Luis"]))
    assert html.count("0 scrabbles · 0 moves · avg 0.0 per move") == 2


def test_turn_log_escapes_word_and_player_and_is_newest_first():
    html = render.turn_log_html(_game())
    assert "<img" not in html
    assert html.count("&lt;img") == 2
    assert html.index("SOL") < html.index("&lt;img")
    assert "Scrabble (all 7 tiles)" in html


def test_turn_log_empty_state():
    assert "No moves yet" in render.turn_log_html(Game("es", ["Ana"]))


def test_ranking_numbers_players_and_marks_single_winner():
    html = render.ranking_html(_game(finished=True))
    assert "1. " in html and "2. " in html
    assert html.count("Winner") == 1 and "Winner (tie)" not in html
    assert "−10 remaining tiles" in html and "+10 went out first" in html
    assert "<img" not in html
    assert html.index("Winner") < html.index("Bo")  # winner is listed first


def test_ranking_marks_tie_for_first_place():
    g = Game("es", ["Ana", "Luis", "Eva"])
    g.add_turn(0, "normal", "A", 10)
    g.add_turn(1, "normal", "B", 10)
    g.finish(["", "", ""])
    html = render.ranking_html(g)
    assert html.count("Winner (tie)") == 2
    assert "1. " in html and "3. " in html


def test_solo_ranking_has_no_winner_badge():
    g = Game("es", ["Ana"])
    g.finish([""])
    assert "Winner" not in render.ranking_html(g)


def test_message_html_escapes_and_clears():
    assert render.message_html("ok", "") == ""
    assert "&lt;b&gt;" in render.message_html("error", "<b>x</b>")
    assert "st-msg-info" in render.message_html("weird-kind", "hi")


def test_header_is_static():
    assert render.header_html().count("st-tile") == 8
