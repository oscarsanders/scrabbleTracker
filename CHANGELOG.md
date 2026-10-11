# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning:
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [2.0.0] - 2026-10-11

Migration from Flask to Python + Gradio, prepared for deployment on Render.

### Added
- Gradio 6 user interface (Home, New game, Play, History, Profile, Admin).
- PostgreSQL support through `DATABASE_URL` (psycopg 3); SQLite remains the
  default for local development and tests.
- `render.yaml` Blueprint, `.python-version`, `.env.example`.
- Pure end-of-game rule module `rules.py`.
- Login throttling, constant-time handling of unknown usernames, security
  event logging with `key=value` context.
- Self-service password change (RF-16); undo and access-control requirements
  documented (RF-17, RF-18).
- Engineering documentation in English: requirements with traceability,
  architecture (with diagrams), ADRs 0002–0004, threat model, risk
  register, deployment guide, security policy.
- GitHub Actions CI (Ruff, mypy, pytest on Python 3.11–3.13, pip-audit),
  Dependabot, issue and pull-request templates.

### Changed
- **Breaking:** Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF and
  Flask-Migrate removed. Plain SQLAlchemy 2.0 with explicit transaction scope.
- **Breaking:** domain codes renamed to English — modes `multijugador` →
  `multiplayer`; statuses `en_curso`/`finalizada` → `in_progress`/`finished`;
  move types `falta`/`pasa`/`cambio` → `foul`/`pass`/`exchange`.
- **Breaking:** accounts are created by the administrator; open
  self-registration is removed (ADR-0004).
- **Breaking:** environment variables: `DATABASE_URL` replaces
  `SCRABBLE_DATABASE_URL`; `SCRABBLE_SECRET_KEY` is no longer used.
- Usernames limited to `A-Za-z0-9._-` (3–32), unique case-insensitively;
  passwords 8–128 characters (was ≥ 6).
- Games: 2–4 players, unique names, validated lengths (PostgreSQL enforces
  them). Business logic that lived in the Flask routes (player-name parsing)
  moved into services.
- User interface text and all documentation are now in English.

### Fixed
- Deleting a user no longer deletes their participations (and therefore the
  scores) in other players' games; it also no longer fails on PostgreSQL when
  the user created games.
- Timestamps use timezone-aware UTC internally (no deprecated `utcnow`).
- Repository referenced `.github/workflows/ci.yml` and `.env.example` that
  did not exist; both are now provided.

### Upgrade notes from 1.x
There is **no automatic data migration**: the database schema and stored
codes differ. If you need to keep v1 data, export it first and open an issue;
a one-off conversion script can be provided.

## [1.0.0] - 2026-09-29
- Flask + SQLite release with layered architecture, CSRF protection and tests.

## [0.1.0] - 2026-09-29
- Initial functional prototype.
