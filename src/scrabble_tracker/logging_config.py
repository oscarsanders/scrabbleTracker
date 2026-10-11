"""Logging configuration (SWEBOK KA06, observability).

Logs go to stdout, which is where Render (and most PaaS) collect them.
Structured context passed through ``logger.info("event", extra={...})``
is appended as ``key=value`` pairs so events stay greppable. Values are
rendered with ``repr`` which also neutralises newlines (log injection).
"""

from __future__ import annotations

import logging
import sys

_STANDARD_ATTRS = frozenset(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__
) | {"message", "asctime"}


class KeyValueFormatter(logging.Formatter):
    """Formatter that appends ``extra`` fields as ``key=value`` pairs."""

    def formatMessage(self, record: logging.LogRecord) -> str:  # noqa: N802
        line = super().formatMessage(record)
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_ATTRS
        }
        if extras:
            pairs = " ".join(f"{key}={extras[key]!r}" for key in sorted(extras))
            line = f"{line} {pairs}"
        return line


def configure_logging(level: str = "INFO") -> None:
    """Configure the ``scrabble_tracker`` logger hierarchy (idempotent)."""
    logger = logging.getLogger("scrabble_tracker")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not any(getattr(h, "_scrabble_handler", False) for h in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            KeyValueFormatter(
                fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
        handler._scrabble_handler = True  # type: ignore[attr-defined]
        logger.addHandler(handler)
    logger.propagate = False
