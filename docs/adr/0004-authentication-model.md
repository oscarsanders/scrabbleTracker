# ADR-0004: Gradio-native authentication with administrator-provisioned accounts

- **Status:** Accepted
- **Date:** 2026-10-11

## Context

v1 offered open self-registration, Flask-Login sessions and CSRF tokens.
Gradio's `launch(auth=callable)` provides a login form, a session cookie, a
`/logout` route and exposes the username as `request.username`, but it has
**no pre-login page where a registration form could live**. Gradio also
documents a custom path: mount the app in FastAPI with an `auth_dependency`.

## Alternatives

| Option | Assessment |
|---|---|
| A. `launch(auth=callable)` backed by the database; admin creates accounts | Minimal code, uses the supported mechanism. Drops open registration. |
| B. FastAPI + session middleware + custom login/register pages + mounted Gradio | Keeps self-registration; more code and more security surface to own (forms, CSRF, cookies). |
| C. Single shared password | Cannot attribute games to users. Rejected. |

## Decision

Option A. For a service exposed to the public Internet, closed registration is
also a safer default (no unsolicited accounts, smaller abuse surface). To
compensate:

- RF-16: users can change their own password (admins set initial passwords).
- RNF-07: in-memory login throttling per username.
- Constant-time-ish behaviour for unknown usernames (`burn_password_check`).
- Usernames restricted to a safe alphabet and unique case-insensitively.

## Consequences

- Positive: small, well-understood implementation; hashes remain compatible
  with v1 (Werkzeug format).
- Negative: no self-service sign-up; sessions live in server memory, so a
  restart or free-tier spin-down signs everyone out; throttling is per process
  and can lock a *known* username temporarily (T-04).
- Upgrade path: Option B if self-registration becomes a requirement; services
  and `auth.Authenticator` are reusable unchanged.
