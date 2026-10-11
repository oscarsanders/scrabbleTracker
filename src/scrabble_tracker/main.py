"""Application entry point: wire configuration, database and UI, then serve.

Run locally with ``python -m scrabble_tracker`` or ``scrabble-tracker``.
On Render the start command is ``python -m scrabble_tracker``.
"""

from __future__ import annotations

import logging

from dotenv import load_dotenv

from scrabble_tracker import __version__
from scrabble_tracker.auth import Authenticator
from scrabble_tracker.config import load_settings
from scrabble_tracker.db import (
    create_db_engine,
    create_session_factory,
    init_db,
    session_scope,
)
from scrabble_tracker.logging_config import configure_logging
from scrabble_tracker.services import accounts
from scrabble_tracker.ui.app import build_demo
from scrabble_tracker.ui.theme import CSS, build_theme

logger = logging.getLogger("scrabble_tracker.main")

#: Number of handler calls Gradio may run in parallel per event.
CONCURRENCY_LIMIT = 10


def main() -> None:
    """Start the web application (blocks until interrupted)."""
    load_dotenv()  # no-op when there is no .env file
    settings = load_settings()
    configure_logging(settings.log_level)
    logger.info(
        "starting",
        extra={
            "version": __version__,
            "environment": settings.environment,
            "host": settings.host,
            "port": settings.port,
        },
    )
    if settings.uses_default_admin_password:
        logger.warning(
            "default_admin_password_in_use",
            extra={"hint": "set SCRABBLE_ADMIN_PASSWORD"},
        )

    engine = create_db_engine(settings.database_url)
    init_db(engine)
    session_factory = create_session_factory(engine)
    with session_scope(session_factory) as session:
        accounts.ensure_admin(
            session, settings.admin_username, settings.admin_password
        )

    demo = build_demo(session_factory)
    demo.queue(default_concurrency_limit=CONCURRENCY_LIMIT)
    # In Gradio 6 ``theme`` and ``css`` are launch() parameters.
    demo.launch(
        server_name=settings.host,
        server_port=settings.port,
        auth=Authenticator(session_factory),
        auth_message="Sign in with the account created for you by the administrator.",
        theme=build_theme(),
        css=CSS,
    )


if __name__ == "__main__":
    main()
