# ADR-0002: Replace Flask with Gradio 6 for the user interface

- **Status:** Accepted
- **Date:** 2026-10-11

> **Update (v3.0.0):** the service layer and database mentioned below were
> removed by [ADR-0005](0005-stateless-single-game.md); the Gradio decision
> itself still stands.

## Context

v1 was a Flask application (blueprints, Jinja2 templates, Flask-Login,
Flask-WTF, Flask-SQLAlchemy). The project owner wants a Python + Gradio
application deployed on Render. Gradio is an event-driven UI framework: there
are no URL routes, form posts, templates or server-side cookie sessions
managed by the application.

## Requirements and constraints

RF-01..RF-18, RNF-01 (mobile), RNF-04 (UI-independent business logic),
R-02 (Gradio ≥ 6). Gradio 6 moved `theme`/`css` from `gr.Blocks()` to
`launch()` and removed `api_name=False`; the API is still evolving.

## Alternatives

| Option | Assessment |
|---|---|
| A. Keep Flask, wrap it in Gradio | Two frameworks, two auth systems; no benefit. |
| B. Rewrite UI in Gradio; keep domain logic | Business logic is already isolated in services/models. Smallest coherent change. |
| C. Gradio mounted inside FastAPI | Allows custom login/registration pages but adds an HTTP layer and more untested surface. Kept as the upgrade path (ADR-0004). |

## Decision

Option B. Remove Flask and all Flask extensions. Keep `tiles`, the closing rule
(now `rules.py`) and the service layer, ported to plain SQLAlchemy 2.0.

Resulting rules:

1. Handlers are thin and return `{component: value}` dictionaries.
2. `ui/render.py` produces escaped HTML and has no Gradio imports.
3. `ui/app.py` avoids `from __future__ import annotations` because Gradio
   injects `gr.Request` by inspecting the annotation object.
4. Dependencies are bounded `gradio>=6.0,<7.0`.

## Consequences

Positive: one Python codebase for UI, simple deployment, free mobile-friendly
widgets. Negative:

- Per-session UI state is lost on reload (the game id is re-selected from
  *Games in progress*).
- No real push updates; players press *Refresh*.
- CSRF/session handling is delegated to Gradio (see `docs/THREAT_MODEL.md`).
- Upgrades across Gradio minor versions can change widget behaviour; the UI
  smoke test and pinned bounds mitigate this.

## Risks

Gradio API drift (R-02 in `docs/RISKS.md`). Review on each Gradio minor
upgrade via Dependabot PRs.
