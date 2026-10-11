"""UI smoke test: the Blocks app builds. Skipped without Gradio."""

import pytest

gr = pytest.importorskip("gradio")


def test_demo_builds():
    from scrabble_tracker.ui.app import build_demo

    assert isinstance(build_demo(), gr.Blocks)


def test_theme_builds():
    from scrabble_tracker.ui.theme import build_theme

    assert build_theme() is not None
