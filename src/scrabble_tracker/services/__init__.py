"""Use cases (business logic), independent from the UI framework.

Services take an open SQLAlchemy ``Session`` as first argument, ``flush``
but never ``commit``; the caller owns the transaction
(see :func:`scrabble_tracker.db.session_scope`).
"""
