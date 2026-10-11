"""Application entry point.

Run locally with ``python -m scrabble_tracker``. On Render the start
command is the same; Render's ``PORT`` is honoured automatically.
"""

from __future__ import annotations

import logging
import os

from scrabble_tracker import __version__
from scrabble_tracker.config import load_settings
from scrabble_tracker.logging_config import configure_logging

logger = logging.getLogger("scrabble_tracker.main")

#: Number of handler calls Gradio may run in parallel per event.
CONCURRENCY_LIMIT = 10


def main() -> None:
    """Start the web application (blocks until interrupted)."""
    # Gradio reads these when it is imported, so set them first.
    os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
    os.environ.setdefault("GRADIO_SSR_MODE", "False")

    from scrabble_tracker.ui.app import build_demo
    from scrabble_tracker.ui.theme import CSS, build_theme

    settings = load_settings()
    configure_logging(settings.log_level)
    logger.info(
        "starting",
        extra={"version": __version__, "host": settings.host, "port": settings.port},
    )

    demo = build_demo()
    demo.queue(default_concurrency_limit=CONCURRENCY_LIMIT)
    # In Gradio 6 ``theme`` and ``css`` are launch() parameters.
    demo.launch(
        server_name=settings.host,
        server_port=settings.port,
        theme=build_theme(),
        css=CSS,
    )


if __name__ == "__main__":
    main()
