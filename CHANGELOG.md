# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [3.0.0] - 2026-10-11

Stateless edition for a first trial on Render (ADR-0005).

### Changed
- **Breaking:** the app now handles **one game per browser session, kept only
  in memory**. Reloading, restarting or the free instance sleeping discards it.
- Settings: no required configuration. On Render (`PORT` present) the app
  binds `0.0.0.0:$PORT` automatically.
- Runtime dependencies reduced to Gradio.
- Domain code moved to the pure `game.py`; `ui/presenter.py` added so what the
  screen shows is unit-tested without Gradio.
- Documentation rewritten for this scope; ADR-0001/0003/0004 marked as parked.

### Removed
- Accounts, authentication, administration, history, statistics.
- Database layer (SQLAlchemy, PostgreSQL support), password hashing, throttling.
- `.env.example`, `SCRABBLE_*` secrets and `DATABASE_URL`.

### Fixed
- Startup on Render no longer depends on `SCRABBLE_ENV`: the previous version
  fell back to development mode and listened on loopback only.

## [2.0.0] - 2026-10-11
Gradio + PostgreSQL edition with accounts (see Git history).

## [1.0.0] - 2026-09-29
Flask + SQLite release.
