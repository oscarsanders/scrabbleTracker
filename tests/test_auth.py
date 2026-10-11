"""auth.py: login adapter with throttling (RF-02, RNF-07)."""

from scrabble_tracker.auth import Authenticator
from scrabble_tracker.db import session_scope
from scrabble_tracker.security import LoginThrottle
from scrabble_tracker.services import accounts


def _setup(session_factory):
    with session_scope(session_factory) as s:
        accounts.create_user(s, "alice", "secret-pass-1")
    return Authenticator(session_factory, LoginThrottle(max_failures=3))


def test_valid_and_invalid_credentials(session_factory):
    auth = _setup(session_factory)
    assert auth("Alice", "secret-pass-1") is True
    assert auth("alice", "nope") is False
    assert auth("ghost", "secret-pass-1") is False


def test_lockout_blocks_even_the_correct_password(session_factory):
    auth = _setup(session_factory)
    for _ in range(3):
        assert auth("alice", "bad") is False
    assert auth("alice", "secret-pass-1") is False


def test_success_clears_failures(session_factory):
    auth = _setup(session_factory)
    auth("alice", "bad")
    auth("alice", "bad")
    assert auth("alice", "secret-pass-1") is True
    auth("alice", "bad")
    auth("alice", "bad")
    assert auth("alice", "secret-pass-1") is True
