"""Exception shared by the domain and the UI.

Its message is user-facing: the UI shows it next to the form, so it must
never contain internal details.
"""

from __future__ import annotations


class DomainError(ValueError):
    """A business rule or an input validation was violated."""
