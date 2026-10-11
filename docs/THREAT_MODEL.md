# Threat model — stateless edition

Lightweight STRIDE review (SWEBOK v4 KA13). The app stores nothing and has no
accounts, so the attack surface is small; it is still reachable from the
Internet, which is why these items are tracked.

| ID | Threat | Mitigation | Evidence | Residual risk |
|---|---|---|---|---|
| T-01 | Stored/reflected XSS through names or words | Every dynamic value is `html.escape`d in `ui/render.py`. | `test_render` | New renderers must keep using `esc()`. |
| T-02 | Seeing or changing another visitor's game | Game lives in a per-session `gr.State`; no shared or global game. | `test_game::test_each_game_is_independent`; ADR-0005 | Relies on Gradio's session isolation. |
| T-03 | Resource exhaustion (huge inputs, endless moves, many sessions) | Bounds on players, name/word/rack length and moves per game. | `test_game` (validation, turn limit) | No per-IP rate limiting; the free instance can be overwhelmed. |
| T-04 | Direct calls to Gradio's HTTP API | Endpoints only act on the caller's own session state and validate every input in `game.py`. | Design | Same as T-02/T-03. |
| T-05 | Vulnerable dependencies | One runtime dependency (Gradio, bounded `<7.0`); Dependabot. | `pyproject.toml`, `.github/dependabot.yml` | No lock file (R-06). |
| T-06 | Information disclosure | Nothing sensitive exists: no credentials, no database, no personal data beyond names typed by the visitor, discarded with the session. | Design | None. |

Out of scope: authentication (none by design), HTTP security headers and TLS
(handled by Gradio/Render).
