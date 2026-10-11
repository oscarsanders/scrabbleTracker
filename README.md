# Scrabble Tracker

[![CI](https://github.com/YOUR-USER/scrabbleMonitor/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR-USER/scrabbleMonitor/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)

A mobile-friendly web app (**Python + Gradio**) to record, score and analyse
Scrabble games, with the board's colour palette. Deployable on
[Render](https://render.com) in one step.

> Replace `YOUR-USER` in the badge URLs (and the deploy button below) with your
> GitHub user or organisation.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR-USER/scrabbleMonitor)

## Features

- **Accounts** created by an administrator; sign-in, password change, profile
  with statistics (games, average, best score, bingos, wins) and full history.
- **Games** in multiplayer (2–4 players, registered users or guests) or solo mode,
  in Spanish or English tile values.
- **Live scoring:** word + points, bingo, foul, pass, exchange, undo, running
  scoreboard and game average.
- **Closing rule:** enter remaining tiles; penalties are deducted and the
  player who went out first receives the others' tile values; final ranking.
- **Security basics:** salted password hashes, login throttling, escaped output,
  server-side authorisation, fail-fast production configuration.

## Quick start (local)

```bash
git clone https://github.com/YOUR-USER/scrabbleMonitor.git
cd scrabbleMonitor
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
python -m scrabble_tracker
```

Open <http://127.0.0.1:7860> and sign in as `admin` / `admin1234` (development
default; the app logs a warning). Create player accounts in the **Admin** tab.
To use it from a phone on the same Wi-Fi set `SCRABBLE_HOST=0.0.0.0`.

## Deploy on Render

1. Push this repository to GitHub.
2. Render → **New → Blueprint** → select the repo (`render.yaml` is detected).
3. Enter `SCRABBLE_ADMIN_PASSWORD` when prompted and deploy.

> ⚠️ **Free tier caveats.** The free web service sleeps after 15 min idle, and
> the **free PostgreSQL database expires after 30 days with no backups**.
> Upgrade the database or use an external Postgres before keeping real data.
> Details: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Project layout

```
src/scrabble_tracker/
  main.py, __main__.py   Composition root and entry point
  config.py              Environment-based settings (fail-fast in production)
  db.py, models.py       SQLAlchemy 2.0 engine/sessions and entities
  rules.py, tiles.py     Pure domain logic (closing rule, tile values)
  security.py, auth.py   Hashing, throttling, Gradio login adapter
  services/              Use cases: accounts.py, games.py
  views.py               Read-only DTOs
  ui/                    Gradio app, pure HTML renderers, theme
tests/                   pytest suite
docs/                    Engineering documentation
render.yaml              Render Blueprint
.github/                 CI, Dependabot, templates
```

## Documentation

| Document | Content |
|---|---|
| [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) | Functional/non-functional requirements traced to code and tests. |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Views, layering, quality attributes. |
| [`docs/adr/`](docs/adr) | Architecture decision records (0001–0004). |
| [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) | STRIDE-style threat model. |
| [`docs/RISKS.md`](docs/RISKS.md) | Risk register and manual smoke test. |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Render runbook, configuration, backups, rollback. |
| [`CONTRIBUTING.md`](CONTRIBUTING.md), [`SECURITY.md`](SECURITY.md), [`CHANGELOG.md`](CHANGELOG.md) | Process and history. |

Engineering approach: SWEBOK Guide v4 knowledge areas, with documentation
practices inspired by ISO/IEC/IEEE 29148 (requirements) and 42010 (architecture)
and ISO/IEC 25010 quality attributes. This is guidance, not a certification.

## Quality gates

```bash
ruff check src tests
mypy src
pytest --cov
```

The same three steps run in GitHub Actions on every push and pull request.

## Status

Version 2.0.0 is a migration from the Flask release. Read
[`docs/RISKS.md`](docs/RISKS.md) (R-07) and run the manual smoke test before
the first production deployment.

## License

MIT — see [`LICENSE`](LICENSE).
