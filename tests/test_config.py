import logging

import pytest

from carbon.config import Config

root_logger = logging.getLogger(__name__)


def test_configure_logger_with_invalid_level_raises_error():
    with pytest.raises(
        ValueError, match="'INVALID_LOG_LEVEL' is not a valid Python logging level"
    ):
        Config(log_level="INVALID_LOG_LEVEL")


def test_configure_logger_info_level_or_higher(caplog):
    Config(log_level="INFO")
    assert root_logger.getEffectiveLevel() == 20  # noqa: PLR2004
    assert "Logger 'root' configured with level=INFO" in caplog.text


def test_configure_logger_debug_level_or_lower(caplog):
    root_logger = logging.getLogger()
    Config(log_level="DEBUG")
    assert root_logger.getEffectiveLevel() == 10  # noqa: PLR2004
    assert "Logger 'root' configured with level=DEBUG" in caplog.text


def test_configure_sentry_no_env_variable(caplog, monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    Config()
    assert "No Sentry DSN found, exceptions will not be sent to Sentry" in caplog.text


def test_configure_sentry_env_variable_is_none(caplog, monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "None")
    Config()
    assert "No Sentry DSN found, exceptions will not be sent to Sentry" in caplog.text


def test_configure_sentry_env_variable_is_dsn(caplog, monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "https://1234567890@00000.ingest.sentry.io/123456")
    Config()
    assert (
        "Sentry DSN found, exceptions will be sent to Sentry with env=test" in caplog.text
    )


def test_load_config_values_success(config):
    assert config.FEED_TYPE == "test_feed_type"
