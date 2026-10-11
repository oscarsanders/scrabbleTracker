"""tiles.py: RF-11, RF-13."""

from scrabble_tracker.tiles import SUPPORTED_LANGUAGES, rack_value, tile_value


def test_supported_languages():
    assert set(SUPPORTED_LANGUAGES) == {"es", "en"}


def test_tile_value_spanish_common_letters():
    assert tile_value("a", "es") == 1
    assert tile_value("Z", "es") == 10


def test_tile_value_unknown_letter_defaults_to_zero():
    assert tile_value("#", "es") == 0


def test_rack_value_simple_letters():
    assert rack_value("AEIOU", "es") == 5


def test_rack_value_spanish_digraphs():
    assert rack_value("CH", "es") == 5
    assert rack_value("LL", "es") == 8


def test_digraphs_are_not_special_in_english():
    assert rack_value("CH", "en") == 3 + 4


def test_rack_value_empty_and_whitespace():
    assert rack_value("", "es") == 0
    assert rack_value("   ", "es") == 0


def test_rack_value_english_and_blank_tile():
    assert rack_value("QZ", "en") == 20
    assert rack_value("?", "en") == 0


def test_rack_value_ignores_inner_spaces_and_case():
    assert rack_value("a e", "en") == 2
