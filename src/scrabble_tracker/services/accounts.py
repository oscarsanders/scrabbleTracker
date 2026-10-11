"""Account use cases: users, authentication, administration (RF-01 .. RF-05)."""

from __future__ import annotations

import logging
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from scrabble_tracker.errors import AuthorizationError, DomainError, NotFoundError
from scrabble_tracker.models import Game, User
from scrabble_tracker.security import (
    burn_password_check,
    hash_password,
    verify_password,
)

logger = logging.getLogger("scrabble_tracker.accounts")

USERNAME_PATTERN = re.compile(r"[A-Za-z0-9_.-]{3,32}")
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def validate_username(raw: str) -> str:
    """Return the trimmed username or raise :class:`DomainError`.

    Usernames are restricted to a safe alphabet: they are displayed in
    the UI and are typed as comma-separated lists when starting a game.
    """
    username = (raw or "").strip()
    if not USERNAME_PATTERN.fullmatch(username):
        raise DomainError(
            "Username must be 3-32 characters: letters, digits, '.', '_' or '-'."
        )
    return username


def validate_password(raw: str) -> None:
    """Raise :class:`DomainError` if ``raw`` is not an acceptable password."""
    if raw is None or len(raw) < MIN_PASSWORD_LENGTH:
        raise DomainError(
            f"Password must have at least {MIN_PASSWORD_LENGTH} characters."
        )
    if len(raw) > MAX_PASSWORD_LENGTH:
        raise DomainError(
            f"Password must have at most {MAX_PASSWORD_LENGTH} characters."
        )


def find_user(session: Session, username: str) -> User | None:
    """Case-insensitive lookup (mobile keyboards auto-capitalise)."""
    wanted = (username or "").strip().lower()
    if not wanted:
        return None
    stmt = select(User).where(func.lower(User.username) == wanted)
    return session.scalars(stmt).first()


def create_user(
    session: Session, username: str, password: str, *, is_admin: bool = False
) -> User:
    """Create an account (RF-01, RF-05).

    Raises:
        DomainError: invalid username/password or username already taken
            (comparison is case-insensitive).
    """
    name = validate_username(username)
    validate_password(password)
    if find_user(session, name) is not None:
        raise DomainError("That username is already taken.")
    user = User(username=name, password_hash=hash_password(password), is_admin=is_admin)
    session.add(user)
    session.flush()
    logger.info("user_created", extra={"user_id": user.id, "is_admin": is_admin})
    return user


def authenticate(session: Session, username: str, password: str) -> User | None:
    """Return the user if the credentials are valid, else ``None``.

    Spends comparable time whether or not the username exists.
    """
    user = find_user(session, username)
    if user is None:
        burn_password_check(password or "")
        return None
    return user if verify_password(password or "", user.password_hash) else None


def require_user(session: Session, username: str | None) -> User:
    """Resolve the authenticated username to a :class:`User`.

    The UI framework authenticates the request; this call only maps the
    name to an entity and fails closed if it cannot (for example when the
    account was deleted while a session was open).
    """
    if not username:
        raise AuthorizationError("You must be logged in.")
    user = find_user(session, username)
    if user is None:
        raise AuthorizationError("Your account no longer exists. Please log in again.")
    return user


def change_password(
    session: Session, user: User, current_password: str, new_password: str
) -> None:
    """Let a user replace their own password (re-verifying the old one)."""
    if not verify_password(current_password or "", user.password_hash):
        raise DomainError("Current password is incorrect.")
    validate_password(new_password)
    user.password_hash = hash_password(new_password)
    session.flush()
    logger.info("password_changed", extra={"user_id": user.id})


def require_admin(actor: User) -> None:
    if not actor.is_admin:
        raise AuthorizationError("Administrator privileges required.")


def list_users(session: Session, *, actor: User) -> list[User]:
    """All users ordered by name. Administrators only."""
    require_admin(actor)
    return list(session.scalars(select(User).order_by(func.lower(User.username))))


def create_user_as_admin(
    session: Session, *, actor: User, username: str, password: str
) -> User:
    """Create a regular account on behalf of an administrator (RF-05)."""
    require_admin(actor)
    return create_user(session, username, password)


def delete_user(session: Session, *, actor: User, user_id: int) -> User:
    """Delete an account (RF-05).

    Game history is preserved: the user's participations become guest
    entries carrying their former name, and games they created are kept
    with no creator. Deleting the administrator is refused.
    """
    require_admin(actor)
    target = session.get(User, user_id)
    if target is None:
        raise NotFoundError("User not found.")
    if target.is_admin:
        raise DomainError("The administrator account cannot be deleted.")

    for participation in list(target.game_players):
        participation.guest_name = target.username
        participation.user = None
    for game in session.scalars(select(Game).where(Game.created_by_id == target.id)):
        game.created_by = None
    session.flush()

    session.delete(target)
    session.flush()
    logger.info("user_deleted", extra={"user_id": user_id, "by": actor.id})
    return target


def ensure_admin(session: Session, username: str, password: str) -> User:
    """Create the bootstrap administrator if missing (idempotent, RF-05)."""
    existing = find_user(session, username)
    if existing is None:
        return create_user(session, username, password, is_admin=True)
    if not existing.is_admin:
        existing.is_admin = True
        session.flush()
    return existing
