# Contributing

Thanks for helping. The process is intentionally light but the quality gates are
real.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

## Workflow

1. Branch from `main`: `git checkout -b feature/short-description`.
2. Write or update tests first when you can (`tests/`).
3. Run the gates locally:
   ```bash
   ruff check src tests
   mypy src
   pytest --cov
   ```
4. Update `CHANGELOG.md` (**Unreleased**) and, if behaviour changed,
   `docs/REQUIREMENTS.md`.
5. Open a pull request to `main`. CI must be green.

## Architecture rules

- Business logic goes in `services/`, `rules.py`, `tiles.py` — **never** in
  `ui/app.py`. Handlers stay thin.
- `services/` must not import Gradio; `ui/render.py` must not import Gradio or
  the database.
- Services `flush`, never `commit`; the caller owns the transaction.
- Escape every dynamic value rendered into HTML with `ui/render.py::esc`.
- Authorise in services, not in the UI.
- Do not use `from __future__ import annotations` in `ui/app.py`
  (see ADR-0002).
- Gradio 6 API: `theme`/`css` are passed to `launch()`.

## Style

PEP 8/257 enforced by Ruff (line length 88). Type hints on new or changed
functions. Comments explain *why*, not *what*.

## Architectural decisions

Changes that affect a documented decision (database, framework, authentication,
hosting) need a new ADR in `docs/adr/` using the template: Context →
Alternatives → Decision → Consequences → Risks.

## Schema changes

Until Alembic is introduced (`docs/RISKS.md`, R-05) models must not change in a
way that requires altering existing tables. Introduce Alembic in the same pull
request as the first such change.

## Commit messages

Imperative present tense, one logical change per commit
(`Add password change use case`). Reference issues with `#123`.
