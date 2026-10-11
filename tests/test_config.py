"""config.py: secure configuration, RNF-02 and deployment (ADR-0003)."""

import pytest

from scrabble_tracker.config import (
    ConfigurationError,
    load_settings,
    normalize_database_url,
)

PROD = {
    "SCRABBLE_ENV": "production",
    "DATABASE_URL": "postgresql://u:p@h/db",
    "SCRABBLE_ADMIN_PASSWORD": "a-strong-password",
}


def test_development_defaults():
    s = load_settings({})
    assert s.environment == "development"
    assert s.database_url.startswith("sqlite:///")
    assert s.host == "127.0.0.1" and s.port == 7860
    assert s.uses_default_admin_password


def test_testing_uses_memory_database():
    assert load_settings({"SCRABBLE_ENV": "testing"}).database_url.endswith(":memory:")


def test_production_valid_binds_all_interfaces_and_uses_port():
    s = load_settings({**PROD, "PORT": "10000"})
    assert s.is_production and s.host == "0.0.0.0"  # noqa: S104
    assert s.port == 10000
    assert s.database_url.startswith("postgresql+psycopg://")


def test_production_requires_database_url():
    env = {k: v for k, v in PROD.items() if k != "DATABASE_URL"}
    with pytest.raises(ConfigurationError, match="DATABASE_URL"):
        load_settings(env)


@pytest.mark.parametrize("password", ["", "admin1234", "short"])
def test_production_rejects_weak_admin_password(password):
    with pytest.raises(ConfigurationError, match="ADMIN_PASSWORD"):
        load_settings({**PROD, "SCRABBLE_ADMIN_PASSWORD": password})


def test_invalid_environment_and_port():
    with pytest.raises(ConfigurationError):
        load_settings({"SCRABBLE_ENV": "staging"})
    with pytest.raises(ConfigurationError):
        load_settings({"PORT": "abc"})
    with pytest.raises(ConfigurationError):
        load_settings({"PORT": "70000"})


def test_password_is_not_in_repr():
    assert "a-strong-password" not in repr(load_settings(PROD))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("postgres://u:p@h/d", "postgresql+psycopg://u:p@h/d"),
        ("postgresql://u:p@h/d", "postgresql+psycopg://u:p@h/d"),
        ("postgresql+psycopg://u:p@h/d", "postgresql+psycopg://u:p@h/d"),
        ("sqlite:///x.db", "sqlite:///x.db"),
    ],
)
def test_normalize_database_url(raw, expected):
    assert normalize_database_url(raw) == expected
