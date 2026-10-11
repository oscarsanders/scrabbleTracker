# ADR-0005: Stateless edition — one in-memory game per browser session

- **Status:** Accepted
- **Date:** 2026-10-11

## Context

Version 2.0.0 added accounts, PostgreSQL, game history and statistics. The
owner wants to *try the app on Render first* with the least possible moving
parts: no database, no accounts, no stored data, and support for a single
game only.

## Alternatives

| Option | Assessment |
|---|---|
| A. Keep v2.0.0 and configure PostgreSQL | Needs a database, secrets and more setup; blocks a quick trial. |
| B. One global in-memory game shared by everyone | Simplest code, but every visitor would see and modify the same game. Rejected. |
| C. One in-memory game **per browser session** (`gr.State`) | No storage, no shared state, no accounts needed. Chosen. |
| D. Persist the game in the browser (local storage) | Survives reloads, but relies on Gradio features not yet verified here; deferred. |

## Decision

Option C. The `Game` object (`game.py`) is plain Python, held in a
per-session `gr.State`. Removed: accounts, authentication, administration,
history, statistics, database, SQLAlchemy/psycopg/Werkzeug/dotenv.
Kept: Gradio UI, tile values, closing rule, validation, tests, CI.

## Consequences

- Positive: zero configuration on Render; nothing sensitive is stored; the
  domain is pure Python and fully unit-tested; one dependency (Gradio).
- Negative: **a game is lost on page reload, when the tab session ends, when
  the server restarts, and when the free instance spins down after ~15
  minutes without traffic.** No history or statistics. Anyone with the URL
  can use the app (there is nothing to protect).
- Reversal: the full version is tagged/branched as 2.0.0; ADR-0003 and
  ADR-0004 describe how persistence and accounts were designed.
