# ADR-0003: PostgreSQL for production, SQLite for development and tests

- **Status:** Parked — not implemented in v3.0.0 (see [ADR-0005](0005-stateless-single-game.md)). Valid again if persistence returns.
- **Date:** 2026-10-11

## Context

Render web services have an **ephemeral filesystem**: local files, including a
SQLite database, are lost on every redeploy, restart and (free tier) spin-down.
Persistent disks need a paid instance type. Render's free PostgreSQL has
constraints: 1 GB, **expires 30 days after creation**, no backups
(source: Render docs, "Deploy for Free", checked 2026-10-11).

## Alternatives

| Option | Assessment |
|---|---|
| A. SQLite on a paid Render persistent disk | Works, but requires a paid instance and ties the data to one disk. |
| B. Render PostgreSQL (free) | Zero cost; **data deleted after the 30-day expiry** unless upgraded. Good for demos. |
| C. Render PostgreSQL (paid) | Durable, backups; recurring cost. |
| D. External managed PostgreSQL | Any provider; configure `DATABASE_URL` manually. |

## Decision

Support PostgreSQL through `DATABASE_URL` via SQLAlchemy and psycopg 3;
keep SQLite as the zero-setup default for development and the test suite.
`render.yaml` provisions option B so the deployment works out of the box;
`docs/DEPLOYMENT.md` documents moving to C or D before keeping real data.

Implementation rules:

- Production **requires** `DATABASE_URL` (no implicit SQLite).
- `postgres://` and `postgresql://` URLs are rewritten to `postgresql+psycopg://`.
- SQLite connections enable `PRAGMA foreign_keys=ON` so dev/test behave like
  PostgreSQL regarding referential integrity.
- Column lengths and constraints are validated in services because PostgreSQL
  enforces `VARCHAR(n)` while SQLite does not.

## Consequences

Positive: durable data in production; dev/prod parity for constraints.
Negative: free-tier expiry is an operational risk (R-01); schema evolution
needs Alembic before the first schema change (R-05).
