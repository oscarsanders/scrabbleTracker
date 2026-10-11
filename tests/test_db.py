"""db.py: transaction scope and engine behaviour."""

import pytest

from scrabble_tracker.db import (
    create_db_engine,
    create_session_factory,
    init_db,
    session_scope,
)
from scrabble_tracker.models import User


def test_session_scope_commits_and_rolls_back():
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    factory = create_session_factory(engine)

    with session_scope(factory) as s:
        s.add(User(username="kept", password_hash="x"))
    with pytest.raises(RuntimeError), session_scope(factory) as s:
        s.add(User(username="lost", password_hash="x"))
        s.flush()
        raise RuntimeError("boom")

    with session_scope(factory) as s:
        names = [u.username for u in s.query(User)]
    assert names == ["kept"]


def test_foreign_keys_are_enforced_on_sqlite():
    from sqlalchemy.exc import IntegrityError

    from scrabble_tracker.models import Game

    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    factory = create_session_factory(engine)
    with pytest.raises(IntegrityError), session_scope(factory) as s:
        s.add(Game(created_by_id=999))


def test_file_database_creates_parent_directory(tmp_path):
    target = tmp_path / "nested" / "dir" / "app.db"
    engine = create_db_engine(f"sqlite:///{target}")
    init_db(engine)
    assert target.exists()
    engine.dispose()
