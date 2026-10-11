"""Visual identity: Scrabble board green and tile cream (RNF-01).

The CSS targets the custom ``st-*`` classes emitted by ``render.py`` plus
a few Gradio containers. It is passed to ``launch(css=...)``: Gradio 6
moved ``theme``/``css`` from ``gr.Blocks`` to ``launch`` (ADR-0002).
"""

from __future__ import annotations

CSS = """
:root {
  --st-board: #0b6e4f;
  --st-board-dark: #084f39;
  --st-tile: #f2e2ba;
  --st-tile-dark: #e3cd94;
  --st-wood: #7a4a2b;
  --st-ink: #262220;
  --st-muted: #6b6459;
  --st-ok: #2f8f56;
  --st-error: #c0392b;
}
.gradio-container { max-width: 760px !important; margin: 0 auto !important; }

.st-header { display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: .5rem; background: var(--st-board-dark);
  padding: .6rem 1rem; border-radius: 10px; }
.st-brand { display: flex; gap: 4px; }
.st-tile { background: var(--st-tile); color: var(--st-wood); font-weight: 700;
  width: 26px; height: 26px; display: flex; align-items: center;
  justify-content: center; border-radius: 4px;
  box-shadow: 0 2px 0 var(--st-tile-dark); font-size: .9rem; }
.st-user { color: var(--st-tile); font-size: .92rem; }

.st-card { background: var(--st-tile); color: var(--st-ink); border-radius: 10px;
  padding: 1rem; margin: .5rem 0; box-shadow: 0 3px 0 var(--st-tile-dark); }
.st-card h3 { margin: 0 0 .25rem 0; color: var(--st-board-dark); }
.st-muted { color: var(--st-muted); font-size: .88rem; }

.st-player { display: flex; justify-content: space-between; align-items: center;
  background: #fff8e6; border-radius: 8px; padding: .55rem .8rem; margin: .4rem 0;
  border-left: 5px solid var(--st-tile-dark); }
.st-player.st-leader { border-left-color: var(--st-board); }
.st-score { font-size: 1.6rem; font-weight: 700; color: var(--st-board-dark); }

.st-table-wrap { overflow-x: auto; }
.st-card table { width: 100%; border-collapse: collapse; color: var(--st-ink); }
.st-card th, .st-card td { text-align: left; padding: .4rem .5rem;
  border-bottom: 1px solid var(--st-tile-dark); font-size: .92rem; }

.st-badge { display: inline-block; padding: .1rem .5rem; border-radius: 999px;
  font-size: .78rem; background: var(--st-tile-dark); color: var(--st-ink); }
.st-badge-scrabble { background: #3f6fae; color: #fff; }
.st-badge-foul { background: var(--st-error); color: #fff; }
.st-badge-admin { background: var(--st-tile); color: var(--st-wood); }

.st-stats { display: flex; flex-wrap: wrap; gap: .6rem; margin-top: .5rem; }
.st-stat { flex: 1 1 110px; background: #fff8e6; border-radius: 8px;
  padding: .6rem; display: flex; flex-direction: column; align-items: center; }
.st-stat-value { font-size: 1.5rem; font-weight: 700; color: var(--st-board-dark); }

.st-msg { padding: .6rem .8rem; border-radius: 8px; font-size: .92rem;
  margin: .3rem 0; }
.st-msg-ok { background: #e3f4ea; color: #1d5c37; }
.st-msg-error { background: #fbe4e1; color: #8a2a1f; }
.st-msg-info { background: #e8eef8; color: #2c4a78; }
"""


def build_theme():
    """Gradio theme in board green with tile-cream accents."""
    import gradio as gr

    return gr.themes.Soft(
        primary_hue="emerald",
        secondary_hue="amber",
        neutral_hue="stone",
    )
