"""Database engine, session factory and transaction scope.

The transaction boundary is the *use case*: services only ``flush``;
the caller opens :func:`session_scope`, which commits on success and
rolls back on any exception.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from scrabble_tracker.models import Base


def create_db_engine(database_url: str) -> Engine:
    """Create an engine tuned for SQLite (dev/test) or PostgreSQL (prod)."""
    url = make_url(database_url)

    if url.get_backend_name() == "sqlite":
        kwargs: dict[str, Any] = {"connect_args": {"check_same_thread": False}}
        if url.database in (None, "", ":memory:"):
            # One shared connection, otherwise every checkout would see
            # its own empty in-memory database.
            kwargs["poolclass"] = StaticPool
        else:
            Path(url.database).parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(url, **kwargs)

        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection: Any, _record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return engine

    # pre_ping/recycle: managed Postgres may restart or drop idle connections.
    return create_engine(url, pool_pre_ping=True, pool_recycle=300)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Return a session factory bound to ``engine``."""
    return sessionmaker(bind=engine, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    """Create missing tables.

    Note: this does not alter existing tables. Adopt Alembic before the
    first schema change in production (see ``docs/RISKS.md``, R-05).
    """
    Base.metadata.create_all(engine)


@contextlib.contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """Provide a transactional scope: commit on success, rollback on error."""
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
