"""Shared fixtures. DB-backed fixtures need SQLAlchemy, so they are lazy."""

from __future__ import annotations

import pytest


@pytest.fixture()
def session():
    """A session on a fresh in-memory SQLite database (FKs enforced)."""
    from scrabble_tracker.db import create_db_engine, create_session_factory, init_db

    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    factory = create_session_factory(engine)
    db_session = factory()
    try:
        yield db_session
    finally:
        db_session.close()
        engine.dispose()


@pytest.fixture()
def session_factory():
    from scrabble_tracker.db import create_db_engine, create_session_factory, init_db

    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    yield create_session_factory(engine)
    engine.dispose()


@pytest.fixture()
def make_user(session):
    """Factory creating users through the real service (validates + hashes)."""
    from scrabble_tracker.services import accounts

    def _make(name: str = "alice", *, admin: bool = False):
        return accounts.create_user(session, name, "secret-pass-1", is_admin=admin)

    return _make
