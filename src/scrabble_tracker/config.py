"""Runtime configuration, read exclusively from environment variables.

Design rules (SWEBOK KA13, secure configuration):

* Secrets never live in the source tree; they come from the environment.
* Production fails fast on unsafe or missing settings instead of
  silently starting with insecure defaults.
* :func:`load_settings` is a pure function of its ``env`` argument so it
  can be unit-tested without touching ``os.environ``.

See ``.env.example`` and ``docs/DEPLOYMENT.md`` for the variable list.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

ENV_DEVELOPMENT = "development"
ENV_TESTING = "testing"
ENV_PRODUCTION = "production"
VALID_ENVIRONMENTS = (ENV_DEVELOPMENT, ENV_TESTING, ENV_PRODUCTION)

#: Convenience password used only outside production (and logged as a warning).
# Dev-only convenience value; production rejects it (see load_settings).
DEFAULT_DEV_ADMIN_PASSWORD = "admin1234"  # noqa: S105
MIN_ADMIN_PASSWORD_LENGTH = 8

DEFAULT_DEV_DATABASE_URL = "sqlite:///data/scrabble.db"
DEFAULT_PORT = 7860


class ConfigurationError(RuntimeError):
    """The environment does not describe a valid, safe configuration."""


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    environment: str
    database_url: str
    admin_username: str
    admin_password: str = field(repr=False)  # never print secrets
    host: str = "127.0.0.1"
    port: int = DEFAULT_PORT
    log_level: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.environment == ENV_PRODUCTION

    @property
    def uses_default_admin_password(self) -> bool:
        return self.admin_password == DEFAULT_DEV_ADMIN_PASSWORD


def normalize_database_url(url: str) -> str:
    """Map PaaS-style PostgreSQL URLs onto the SQLAlchemy psycopg 3 driver.

    Render (like Heroku) may hand out ``postgres://`` or ``postgresql://``
    URLs. SQLAlchemy rejects the first form and would pick the legacy
    psycopg2 driver for the second, so both are rewritten to
    ``postgresql+psycopg://``. Any other URL is returned unchanged.
    """
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


def _parse_port(raw: str) -> int:
    try:
        port = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"Invalid port: {raw!r}") from exc
    if not 1 <= port <= 65535:
        raise ConfigurationError(f"Port out of range: {port}")
    return port


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Build :class:`Settings` from ``env`` (defaults to ``os.environ``).

    Raises:
        ConfigurationError: if the environment is invalid or, in
            production, if a required or unsafe value is detected.
    """
    env = os.environ if env is None else env

    environment = env.get("SCRABBLE_ENV", ENV_DEVELOPMENT).strip().lower()
    if environment not in VALID_ENVIRONMENTS:
        raise ConfigurationError(
            f"SCRABBLE_ENV must be one of {VALID_ENVIRONMENTS}, got {environment!r}."
        )
    production = environment == ENV_PRODUCTION

    database_url = env.get("DATABASE_URL", "").strip()
    admin_username = env.get("SCRABBLE_ADMIN_USERNAME", "").strip() or "admin"
    admin_password = env.get("SCRABBLE_ADMIN_PASSWORD", "")

    if production:
        if not database_url:
            raise ConfigurationError(
                "DATABASE_URL is required in production: the container "
                "filesystem is ephemeral, so an implicit SQLite file would "
                "lose all data on restart."
            )
        if (
            not admin_password
            or admin_password == DEFAULT_DEV_ADMIN_PASSWORD
            or len(admin_password) < MIN_ADMIN_PASSWORD_LENGTH
        ):
            raise ConfigurationError(
                "SCRABBLE_ADMIN_PASSWORD must be set to a non-default value "
                f"of at least {MIN_ADMIN_PASSWORD_LENGTH} characters in production."
            )
    else:
        if not database_url:
            database_url = (
                "sqlite:///:memory:"
                if environment == ENV_TESTING
                else DEFAULT_DEV_DATABASE_URL
            )
        admin_password = admin_password or DEFAULT_DEV_ADMIN_PASSWORD

    # Render requires binding to all interfaces; locally stay on loopback.
    all_interfaces = "0.0.0.0"  # noqa: S104
    host = env.get("SCRABBLE_HOST", "").strip() or (
        all_interfaces if production else "127.0.0.1"
    )
    # ``PORT`` is injected by Render; ``SCRABBLE_PORT`` is for local use.
    port = _parse_port(
        env.get("PORT", "").strip()
        or env.get("SCRABBLE_PORT", "").strip()
        or str(DEFAULT_PORT)
    )
    log_level = env.get("SCRABBLE_LOG_LEVEL", "INFO").strip().upper() or "INFO"

    return Settings(
        environment=environment,
        database_url=normalize_database_url(database_url),
        admin_username=admin_username,
        admin_password=admin_password,
        host=host,
        port=port,
        log_level=log_level,
    )
