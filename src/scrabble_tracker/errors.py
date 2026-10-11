"""Exception hierarchy shared by the service layer and the UI layer.

The UI layer catches :class:`DomainError` (and its subclasses) and shows
the message to the user; any other exception is treated as a bug.
Messages of these exceptions are therefore user-facing and must never
contain secrets or internal details.
"""

from __future__ import annotations


class DomainError(ValueError):
    """A business rule or an input validation was violated."""


class NotFoundError(DomainError):
    """The entity does not exist *or is not visible to the acting user*.

    Both situations deliberately share one error so that callers cannot
    probe for the existence of other users' games (IDOR hardening).
    """


class AuthorizationError(DomainError):
    """The acting user is not allowed to perform the operation."""
