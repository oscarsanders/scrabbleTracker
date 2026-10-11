"""security.py: RNF-02, RNF-07."""

from scrabble_tracker.security import (
    LoginThrottle,
    burn_password_check,
    hash_password,
    verify_password,
)


def test_hash_is_salted_and_verifiable():
    h1, h2 = hash_password("correct horse"), hash_password("correct horse")
    assert h1 != h2 and "correct horse" not in h1
    assert verify_password("correct horse", h1)
    assert not verify_password("wrong", h1)


def test_burn_password_check_does_not_raise():
    burn_password_check("anything")


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def _throttle(clock):
    return LoginThrottle(
        max_failures=3, window_seconds=60, lockout_seconds=120, clock=clock
    )


def test_locks_after_max_failures_then_unlocks():
    clock = FakeClock()
    t = _throttle(clock)
    for _ in range(2):
        t.record_failure("bob")
    assert not t.is_locked("bob")
    t.record_failure("bob")
    assert t.is_locked("bob")
    clock.now += 121
    assert not t.is_locked("bob")


def test_old_failures_expire_from_window():
    clock = FakeClock()
    t = _throttle(clock)
    t.record_failure("bob")
    t.record_failure("bob")
    clock.now += 61
    t.record_failure("bob")
    assert not t.is_locked("bob")


def test_success_resets_and_keys_are_independent():
    clock = FakeClock()
    t = _throttle(clock)
    t.record_failure("bob")
    t.record_failure("bob")
    t.record_success("bob")
    t.record_failure("bob")
    assert not t.is_locked("bob")
    for _ in range(3):
        t.record_failure("eve")
    assert t.is_locked("eve") and not t.is_locked("bob")


def test_prune_bounds_memory():
    clock = FakeClock()
    t = LoginThrottle(
        max_failures=5, window_seconds=10, clock=clock, max_tracked_keys=5
    )
    for i in range(5):
        t.record_failure(f"k{i}")
    clock.now += 11
    t.record_failure("new")
    assert len(t._failures) == 1
