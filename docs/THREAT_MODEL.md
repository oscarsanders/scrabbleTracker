# Threat model — Scrabble Tracker

Method: lightweight STRIDE review proportional to the system (SWEBOK v4 KA13,
secure-by-design). Re-run it when authentication, hosting or data types change.

## Assets

| Asset | Why it matters |
|---|---|
| Account credentials | Account takeover; admin takeover enables account deletion. |
| Game data | Integrity of scores and history; privacy among groups. |
| Deployment secrets (`SCRABBLE_ADMIN_PASSWORD`, `DATABASE_URL`) | Full control of the app/data. |

## Trust boundaries

Browser ⟷ Render TLS proxy ⟷ app process ⟷ PostgreSQL. Everything coming from
the browser (names, words, tile strings, ids in dropdowns) is untrusted.

## Threats and mitigations

| ID | Threat (STRIDE) | Mitigation | Evidence | Residual risk |
|---|---|---|---|---|
| T-01 | Brute force / credential stuffing (S) | scrypt hashes, ≥ 8-char passwords, per-username throttle (5 failures → 5 min lock), unknown users cost the same time. | `test_security`, `test_auth` | Distributed guessing across many usernames is not rate-limited per IP. |
| T-02 | Stored XSS via player names, words, usernames (T/E) | Every dynamic value is `html.escape`d in `ui/render.py`; usernames restricted to `[A-Za-z0-9._-]`. | `test_render` | New renderers must keep using `esc()`; review in PRs. |
| T-03 | Reading/modifying other users' games by guessing ids (I/T) | `get_game_for_user` on every access; identical error for "missing" and "not yours". | `test_services_games::test_access_control_…` | None known. |
| T-04 | Lock-out of a known username by an attacker (D) | Lock is time-limited (5 min) and resets on restart. | `test_security` | An attacker can keep a known account locked; accepted for this scale. |
| T-05 | Privilege escalation to admin actions (E) | `require_admin` inside services; acting user derived from server-side `request.username`; admin account undeletable. | `test_services_accounts::test_admin_operations_require_admin` | UI hiding of the Admin tab is cosmetic only. |
| T-06 | CSRF / session theft (S/T) | Delegated to Gradio's session cookie and Render's HTTPS. Cookie attributes are **not** controlled or verified by this project. | — | Review Gradio's behaviour on upgrades; keep the app HTTPS-only (Render default). |
| T-07 | Secret leakage via repo, logs or error pages (I) | Secrets only in environment; `.env` git-ignored; `Settings.__repr__` hides the password; logs never include passwords; unexpected errors show a generic message. | `test_config::test_password_is_not_in_repr` | Rotate secrets if a deploy log is ever shared. |
| T-08 | Vulnerable or malicious dependencies (T/E) | Version bounds, Dependabot, `pip-audit` job in CI. | CI | No lock file yet (R-04 in `RISKS.md`). |
| T-09 | Data loss or unavailability (D) | Managed PostgreSQL; documented backups procedure. Free-tier DB expires after 30 days. | `docs/DEPLOYMENT.md` | See R-01/R-03. |
| T-10 | Calling Gradio's HTTP API directly (E) | All Gradio endpoints sit behind the login and every handler re-authorises. Hiding endpoints (`api_visibility`) is **not** relied upon: Gradio documents that it is not a security control. | Design | Same as T-06. |

## Not covered

HTTP security headers (set by Gradio/Render, not by this code), per-IP rate
limiting, account recovery by e-mail (the admin resets access), audit
retention beyond Render's log retention.
