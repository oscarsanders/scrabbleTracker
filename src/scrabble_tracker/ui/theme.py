"""Visual identity: Scrabble board green and tile cream.

The CSS targets the custom ``st-*`` classes emitted by ``render.py`` plus
the Gradio container. It is passed to ``launch(css=...)``: Gradio 6 moved
``theme``/``css`` from ``gr.Blocks`` to ``launch`` (ADR-0002).

Dark mode: Gradio recolours text inside ``gr.HTML`` for dark themes, which
made dark-on-cream text turn white. Text colours inside the cream cards are
therefore set with ``!important`` so the cards read the same in both modes.
"""

from __future__ import annotations

CSS = """
:root {
  --st-board: #0b6e4f;
  --st-board-dark: #084f39;
  --st-tile: #f2e2ba;
  --st-tile-dark: #d9c48a;
  --st-wood: #7a4a2b;
  --st-ink: #262220;
  --st-muted: #5f574b;
  --st-gold: #e0a800;
}
.gradio-container { max-width: 980px !important; margin: 0 auto !important; }

/* Header */
.st-header { display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: .5rem; background: var(--st-board-dark);
  padding: .45rem .9rem; border-radius: 10px; }
.st-brand { display: flex; gap: 4px; }
.st-tile { background: var(--st-tile); color: var(--st-wood) !important;
  font-weight: 700; width: 24px; height: 24px; display: flex;
  align-items: center; justify-content: center; border-radius: 4px;
  box-shadow: 0 2px 0 var(--st-tile-dark); font-size: .85rem; }
.st-user { color: var(--st-tile) !important; font-size: .9rem; }

/* Cream cards: force dark text in light AND dark mode */
.st-card { background: var(--st-tile); border-radius: 10px;
  padding: .7rem .9rem; margin: .35rem 0; box-shadow: 0 3px 0 var(--st-tile-dark); }
.st-card, .st-card p, .st-card div, .st-card strong, .st-card td, .st-card th,
.st-card span { color: var(--st-ink) !important; }
.st-card h3 { margin: 0 0 .15rem 0; font-size: 1.05rem;
  color: var(--st-board-dark) !important; }
.st-card .st-muted { color: var(--st-muted) !important; font-size: .85rem;
  margin: 0; }
.st-card .st-score { color: var(--st-board-dark) !important; }

/* Players: responsive grid keeps the board short on wide screens */
.st-players { display: grid; gap: .45rem; margin-top: .4rem;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); }
.st-player { display: flex; justify-content: space-between; align-items: center;
  gap: .5rem; background: #fff8e6; border-radius: 8px; padding: .45rem .7rem;
  border-left: 5px solid var(--st-tile-dark); }
.st-player.st-leader { border-left-color: var(--st-board); }
.st-score { font-size: 1.55rem; font-weight: 700; }

/* Moves table: bounded height, scrolls inside the card */
.st-table-wrap { overflow: auto; max-height: 300px; }
.st-card table { width: 100%; border-collapse: collapse; background: transparent; }
.st-card th, .st-card td { text-align: left; padding: .3rem .45rem;
  font-size: .88rem; background: transparent !important;
  border: 0 !important; border-bottom: 1px solid var(--st-tile-dark) !important; }
.st-card th { position: sticky; top: 0; background: var(--st-tile) !important;
  color: var(--st-board-dark) !important; }

/* Badges */
.st-card .st-badge, .st-badge { display: inline-block; padding: .05rem .5rem;
  border-radius: 999px; font-size: .75rem; background: var(--st-tile-dark);
  color: var(--st-ink) !important; }
.st-card .st-badge-scrabble { background: #3f6fae; color: #fff !important; }
.st-card .st-badge-foul { background: #c0392b; color: #fff !important; }
.st-card .st-badge-winner { background: var(--st-gold); color: #3a2a00 !important;
  font-weight: 700; margin-left: .35rem; }

/* Feedback banners */
.st-msg { padding: .45rem .8rem; border-radius: 8px; font-size: .9rem;
  margin: .2rem 0; }
.st-msg, .st-msg * { color: inherit; }
.st-msg-ok { background: #e3f4ea; color: #1d5c37 !important; }
.st-msg-error { background: #fbe4e1; color: #8a2a1f !important; }
.st-msg-info { background: #e8eef8; color: #2c4a78 !important; }
"""


def build_theme():
    """Gradio theme in board green with tile-cream accents."""
    import gradio as gr

    return gr.themes.Soft(
        primary_hue="emerald",
        secondary_hue="amber",
        neutral_hue="stone",
    )
