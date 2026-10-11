# Contributing

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Workflow

1. Branch from `main`; write or update tests first when you can.
2. Run the gates:
   ```bash
   ruff check src tests
   mypy src
   pytest --cov
   ```
3. Update `CHANGELOG.md` (**Unreleased**) and, if behaviour changed,
   `docs/REQUIREMENTS.md`.
4. Open a pull request; CI must be green.

## Architecture rules

- Business rules go in `game.py`, `rules.py`, `tiles.py` — never in
  `ui/app.py`. Handlers stay thin.
- `game.py`, `rules.py`, `tiles.py`, `ui/render.py` and `ui/presenter.py` must
  not import Gradio.
- Escape every dynamic value rendered into HTML with `ui/render.py::esc`.
- No module-level mutable state: a game belongs to one session only.
- Gradio 6: pass `theme`/`css` to `launch()`; do not use `api_name=False`.

## Decisions

Changes affecting a documented decision (framework, persistence, accounts,
hosting) need a new ADR in `docs/adr/` (Context → Alternatives → Decision →
Consequences).

## Style

PEP 8/257 enforced by Ruff (line length 88); type hints on new code; comments
explain *why*. Commits: imperative present tense, one logical change each.
