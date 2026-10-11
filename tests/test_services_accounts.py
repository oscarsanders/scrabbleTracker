"""services/accounts.py: RF-01, RF-02, RF-05, RNF-02."""

import pytest

from scrabble_tracker.errors import AuthorizationError, DomainError, NotFoundError
from scrabble_tracker.services import accounts, games


def test_create_user_hashes_password(session):
    user = accounts.create_user(session, "alice", "secret-pass-1")
    assert user.password_hash != "secret-pass-1"
    assert accounts.authenticate(session, "alice", "secret-pass-1") is user


@pytest.mark.parametrize("name", ["", "ab", "has space", "semi;colon", "a" * 33, "a,b"])
def test_invalid_usernames_rejected(session, name):
    with pytest.raises(DomainError):
        accounts.create_user(session, name, "secret-pass-1")


def test_short_password_rejected(session):
    with pytest.raises(DomainError):
        accounts.create_user(session, "alice", "short")


def test_duplicate_username_is_case_insensitive(session):
    accounts.create_user(session, "Alice", "secret-pass-1")
    with pytest.raises(DomainError):
        accounts.create_user(session, "alice", "secret-pass-1")


def test_authenticate_is_case_insensitive_on_username_only(session):
    accounts.create_user(session, "Alice", "secret-pass-1")
    assert accounts.authenticate(session, "alice", "secret-pass-1") is not None
    assert accounts.authenticate(session, "alice", "Secret-pass-1") is None
    assert accounts.authenticate(session, "nobody", "secret-pass-1") is None
    assert accounts.authenticate(session, "", "") is None


def test_require_user_fails_closed(session):
    with pytest.raises(AuthorizationError):
        accounts.require_user(session, None)
    with pytest.raises(AuthorizationError):
        accounts.require_user(session, "ghost")


def test_change_password(session, make_user):
    user = make_user()
    with pytest.raises(DomainError):
        accounts.change_password(session, user, "wrong", "new-secret-9")
    with pytest.raises(DomainError):
        accounts.change_password(session, user, "secret-pass-1", "short")
    accounts.change_password(session, user, "secret-pass-1", "new-secret-9")
    assert accounts.authenticate(session, "alice", "new-secret-9") is user


def test_ensure_admin_is_idempotent(session):
    first = accounts.ensure_admin(session, "root", "root-secret-1")
    again = accounts.ensure_admin(session, "root", "other-secret-1")
    assert first is again and first.is_admin


def test_admin_operations_require_admin(session, make_user):
    admin, player = make_user("root", admin=True), make_user("bob")
    with pytest.raises(AuthorizationError):
        accounts.create_user_as_admin(
            session, actor=player, username="eve", password="secret-pass-1"
        )
    with pytest.raises(AuthorizationError):
        accounts.list_users(session, actor=player)
    with pytest.raises(AuthorizationError):
        accounts.delete_user(session, actor=player, user_id=admin.id)
    created = accounts.create_user_as_admin(
        session, actor=admin, username="eve", password="secret-pass-1"
    )
    assert not created.is_admin
    assert [u.username for u in accounts.list_users(session, actor=admin)] == [
        "bob",
        "eve",
        "root",
    ]


def test_admin_cannot_be_deleted_and_missing_user(session, make_user):
    admin = make_user("root", admin=True)
    with pytest.raises(DomainError):
        accounts.delete_user(session, actor=admin, user_id=admin.id)
    with pytest.raises(NotFoundError):
        accounts.delete_user(session, actor=admin, user_id=9999)


def test_delete_user_preserves_other_players_history(session, make_user):
    admin = make_user("root", admin=True)
    bob, carol = make_user("bob"), make_user("carol")
    game = games.start_game(
        session, creator=bob, mode="multiplayer", language="es", other_players="carol"
    )
    games.add_turn(
        session,
        game=game,
        player_id=game.players[0].id,
        turn_type="normal",
        word="CASA",
        points=20,
    )
    accounts.delete_user(session, actor=admin, user_id=bob.id)
    session.expire_all()
    assert game.created_by_id is None
    names = [p.display_name for p in game.players]
    assert names == ["bob", "carol"]
    assert game.players[0].current_score == 20
    assert game.players[1].user_id == carol.id
