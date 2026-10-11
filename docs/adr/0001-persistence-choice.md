# ADR-0001: Persistence technology (SQLite + SQLAlchemy)

- **Status:** Parked — v3.0.0 has no persistence (see [ADR-0005](0005-stateless-single-game.md)). Production design: [ADR-0003](0003-postgresql-for-production.md).
- **Date:** 2026-09-29 (v1.0.0, Flask release)

## Context

Scrabble Tracker stores users, games, players and moves, with simple relational
queries and a low expected volume. v1 ran locally on one machine.

## Alternatives considered

| Option | Description |
|---|---|
| A. SQLite + SQLAlchemy | Embedded single-file database. |
| B. PostgreSQL + SQLAlchemy | Separate database server. |
| C. Flat JSON files | No database engine. |

## Decision

Option A. SQLAlchemy as the abstraction layer keeps a later move to PostgreSQL
a configuration change.

## Consequences

- Positive: zero infrastructure for local use; ACID transactions.
- Negative: single-file store, weak under concurrent writers, no managed backups.

## Review trigger and outcome

The ADR stated it should be revisited when the app is hosted for several
groups. Deploying to Render (ephemeral filesystem) is that trigger: see ADR-0003.
