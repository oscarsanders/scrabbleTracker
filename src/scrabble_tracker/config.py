"""Runtime settings read from environment variables.

The app needs no configuration to run: locally it listens on loopback;
on a platform that sets ``PORT`` (such as Render) it listens on all
interfaces, which the platform's proxy requires.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

DEFAULT_PORT = 7860


class ConfigurationError(RuntimeError):
    """The environment contains an invalid value."""


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    log_level: str = "INFO"


def _parse_port(raw: str) -> int:
    try:
        port = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"Invalid port: {raw!r}") from exc
    if not 1 <= port <= 65535:
        raise ConfigurationError(f"Port out of range: {port}")
    return port


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Build :class:`Settings` from ``env`` (defaults to ``os.environ``)."""
    env = os.environ if env is None else env

    platform_port = env.get("PORT", "").strip()  # injected by Render
    on_platform = bool(platform_port) or env.get("RENDER") == "true"
    all_interfaces = "0.0.0.0"  # noqa: S104
    host = env.get("SCRABBLE_HOST", "").strip() or (
        all_interfaces if on_platform else "127.0.0.1"
    )
    port = _parse_port(
        platform_port or env.get("SCRABBLE_PORT", "").strip() or str(DEFAULT_PORT)
    )
    log_level = env.get("SCRABBLE_LOG_LEVEL", "INFO").strip().upper() or "INFO"
    return Settings(host=host, port=port, log_level=log_level)
