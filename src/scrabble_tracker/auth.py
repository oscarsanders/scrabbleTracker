"""Authentication adapter between Gradio's login form and the account service.

Gradio's ``launch(auth=...)`` accepts a callable ``(username, password)``
returning a boolean. :class:`Authenticator` implements it on top of the
database, with brute-force throttling and security-event logging
(RNF-02, RNF-07). Gradio owns the session cookie after a successful login.
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session, sessionmaker

from scrabble_tracker.db import session_scope
from scrabble_tracker.security import LoginThrottle
from scrabble_tracker.services import accounts

logger = logging.getLogger("scrabble_tracker.auth")


class Authenticator:
    """Callable suitable for ``demo.launch(auth=Authenticator(...))``."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        throttle: LoginThrottle | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._throttle = throttle or LoginThrottle()

    def __call__(self, username: str, password: str) -> bool:
        key = (username or "").strip().lower()

        if self._throttle.is_locked(key):
            # Do not even check the password: avoids a guessing oracle.
            logger.warning("login_blocked", extra={"username": key[:64]})
            return False

        with session_scope(self._session_factory) as session:
            user = accounts.authenticate(session, username, password)
            user_id = user.id if user is not None else None

        if user_id is None:
            self._throttle.record_failure(key)
            logger.warning("login_failed", extra={"username": key[:64]})
            return False

        self._throttle.record_success(key)
        logger.info("login_succeeded", extra={"user_id": user_id})
        return True
