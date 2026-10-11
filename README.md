# Scrabble Tracker

[![CI](https://github.com/YOUR-USER/YOUR-REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR-USER/YOUR-REPO/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A small web app (**Python + Gradio**) to keep score in **one Scrabble game**,
with the board's colour palette. Nothing is stored: no database, no accounts.

> Replace `YOUR-USER/YOUR-REPO` in the badge URLs with your GitHub path.

## What it does

- Start a game with 1–4 players (one name = solo) in Spanish or English tiles.
- Record moves: word, scrabble (all 7 tiles), foul, pass, exchange; undo a player's last move.
- Live scoreboard with the game average and each player's average points per move.
- Finish the game: enter remaining tiles, penalties and the first-out bonus are
  applied, and the final ranking (1–N, with a **Winner** badge) is shown.

> ⚠️ **The game lives only in your browser session.** Reloading the page,
> a server restart, or the free Render instance sleeping (~15 min idle)
> discards it. See [ADR-0005](docs/adr/0005-stateless-single-game.md).

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m scrabble_tracker
```

Open <http://127.0.0.1:7860>.

## Deploy on Render

Blueprint: **New → Blueprint** → select the repo. Or create a Web Service with
Build Command `pip install .` and Start Command `python -m scrabble_tracker`.
No environment variables are needed. Details and troubleshooting:
[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Project layout

```
src/scrabble_tracker/
  main.py, __main__.py   Entry point
  config.py              Host/port from the environment
  game.py                Single-game model (validation, scores, closing)
  rules.py, tiles.py     Closing rule and tile values (pure)
  ui/                    Gradio app, presenter, escaped HTML renderers, theme
tests/                   pytest suite (pure Python; UI smoke test needs Gradio)
docs/                    Requirements, architecture, ADRs, threat model, risks
render.yaml              Render Blueprint
```

## Documentation

| Document | Content |
|---|---|
| [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) | Requirements traced to tests. |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Structure and quality attributes. |
| [`docs/adr/`](docs/adr) | Architecture decision records. |
| [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md), [`docs/RISKS.md`](docs/RISKS.md) | Security and risk register, manual smoke test. |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Render guide. |

Engineering approach: SWEBOK Guide v4, with documentation inspired by
ISO/IEC/IEEE 29148 and 42010 and ISO/IEC 25010. Guidance, not certification.

## Quality gates

```bash
ruff check src tests && mypy src && pytest --cov
```

## License

MIT — see [`LICENSE`](LICENSE).
