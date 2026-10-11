"""UI smoke test: the Blocks app builds and every handler is wired.

Skipped automatically when Gradio is not installed.
"""

import pytest

gr = pytest.importorskip("gradio")


def test_demo_builds(session_factory):
    from scrabble_tracker.ui.app import RACK_SLOTS, build_demo

    demo = build_demo(session_factory)
    assert isinstance(demo, gr.Blocks)
    assert RACK_SLOTS == 4  # on_finish declares exactly four rack parameters


def test_theme_builds():
    from scrabble_tracker.ui.theme import build_theme

    assert build_theme() is not None
