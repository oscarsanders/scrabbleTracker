"""Security primitives: password hashing and login throttling.

Hashing delegates to ``werkzeug.security`` (scrypt by default) instead
of a home-grown scheme, and keeps the hash format used by the original
Flask release so existing hashes remain verifiable.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(raw_password: str) -> str:
    """Return a salted hash of ``raw_password`` (never store plaintext)."""
    return generate_password_hash(raw_password)


def verify_password(raw_password: str, password_hash: str) -> bool:
    """Check ``raw_password`` against a stored hash."""
    return check_password_hash(password_hash, raw_password)


_dummy_hash: str | None = None
_dummy_lock = threading.Lock()


def burn_password_check(raw_password: str) -> None:
    """Spend the same time as a real verification.

    Called when the username does not exist so that response time does
    not reveal which usernames are registered.
    """
    global _dummy_hash
    with _dummy_lock:
        if _dummy_hash is None:
            _dummy_hash = generate_password_hash("not-a-real-password")
        dummy = _dummy_hash
    check_password_hash(dummy, raw_password)


class LoginThrottle:
    """In-memory brute-force mitigation, keyed by an arbitrary string.

    After ``max_failures`` failed attempts inside ``window_seconds`` the
    key is locked for ``lockout_seconds``. State lives in process memory:
    it is reset on restart and is not shared between processes. That is
    acceptable for the single-instance deployment documented in
    ``docs/ARCHITECTURE.md``. Trade-off: an attacker can lock a *known*
    username for a few minutes (see ``docs/THREAT_MODEL.md``, T-04).
    """

    def __init__(
        self,
        max_failures: int = 5,
        window_seconds: float = 300.0,
        lockout_seconds: float = 300.0,
        clock: Callable[[], float] = time.monotonic,
        max_tracked_keys: int = 4096,
    ) -> None:
        self._max_failures = max_failures
        self._window = window_seconds
        self._lockout = lockout_seconds
        self._clock = clock
        self._max_keys = max_tracked_keys
        self._failures: dict[str, list[float]] = {}
        self._locked_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def is_locked(self, key: str) -> bool:
        """Return ``True`` while ``key`` is inside its lockout period."""
        now = self._clock()
        with self._lock:
            until = self._locked_until.get(key)
            if until is None:
                return False
            if now >= until:
                del self._locked_until[key]
                return False
            return True

    def record_failure(self, key: str) -> None:
        """Register a failed attempt, locking ``key`` if the limit is hit."""
        now = self._clock()
        with self._lock:
            if len(self._failures) >= self._max_keys:
                self._prune(now)
            recent = [t for t in self._failures.get(key, []) if now - t < self._window]
            recent.append(now)
            self._failures[key] = recent
            if len(recent) >= self._max_failures:
                self._locked_until[key] = now + self._lockout
                del self._failures[key]

    def record_success(self, key: str) -> None:
        """Forget failures for ``key`` after a successful login."""
        with self._lock:
            self._failures.pop(key, None)
            self._locked_until.pop(key, None)

    def _prune(self, now: float) -> None:
        self._failures = {
            key: [t for t in times if now - t < self._window]
            for key, times in self._failures.items()
        }
        self._failures = {k: v for k, v in self._failures.items() if v}
        self._locked_until = {k: u for k, u in self._locked_until.items() if u > now}
