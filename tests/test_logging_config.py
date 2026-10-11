"""logging_config.py: observability (KA06)."""

import logging

from scrabble_tracker.logging_config import KeyValueFormatter


def _record(**extra):
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "event", (), None)
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_extras_are_appended_sorted():
    fmt = KeyValueFormatter("%(levelname)s %(message)s")
    assert fmt.format(_record(b=2, a="x")) == "INFO event a='x' b=2"


def test_no_extras_leaves_line_untouched():
    assert KeyValueFormatter("%(message)s").format(_record()) == "event"


def test_newlines_in_values_cannot_forge_log_lines():
    line = KeyValueFormatter("%(message)s").format(_record(user="a\nFAKE line"))
    assert "\n" not in line
