# ADR-0001: Persistence technology (SQLite + SQLAlchemy)

- **Status:** Superseded by [ADR-0003](0003-postgresql-for-production.md)
  for production. Still valid for local development and tests.
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
