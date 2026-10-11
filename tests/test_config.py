"""config.py: zero-configuration startup locally and on Render."""

import pytest

from scrabble_tracker.config import ConfigurationError, load_settings


def test_local_defaults_listen_on_loopback():
    s = load_settings({})
    assert (s.host, s.port, s.log_level) == ("127.0.0.1", 7860, "INFO")


def test_render_port_binds_all_interfaces():
    s = load_settings({"PORT": "10000"})
    assert s.host == "0.0.0.0" and s.port == 10000  # noqa: S104


def test_render_flag_alone_binds_all_interfaces():
    assert load_settings({"RENDER": "true"}).host == "0.0.0.0"  # noqa: S104


def test_explicit_overrides():
    s = load_settings(
        {
            "SCRABBLE_HOST": "10.0.0.5",
            "SCRABBLE_PORT": "9000",
            "SCRABBLE_LOG_LEVEL": "debug",
        }
    )
    assert (s.host, s.port, s.log_level) == ("10.0.0.5", 9000, "DEBUG")


def test_platform_port_wins_over_local_port():
    assert load_settings({"PORT": "10000", "SCRABBLE_PORT": "9000"}).port == 10000


@pytest.mark.parametrize("port", ["abc", "0", "70000", "-1"])
def test_invalid_port_rejected(port):
    with pytest.raises(ConfigurationError):
        load_settings({"PORT": port})
