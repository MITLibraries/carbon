import logging

import pytest

from carbon.config import configure_logger, configure_sentry, load_config_values


def test_configure_logger_with_invalid_level_raises_error():
    logger = logging.getLogger(__name__)
    with pytest.raises(ValueError, match="'oops' is not a valid Python logging level"):
        configure_logger(logger, log_level_string="oops")


def test_configure_logger_info_level_or_higher():
    logger = logging.getLogger(__name__)
    result = configure_logger(logger, log_level_string="info")
    assert logger.getEffectiveLevel() == 20  # noqa: PLR2004
    assert result == "Logger 'tests.test_config' configured with level=INFO"


def test_configure_logger_debug_level_or_lower():
    logger = logging.getLogger(__name__)
    result = configure_logger(logger, log_level_string="DEBUG")
    assert logger.getEffectiveLevel() == 10  # noqa: PLR2004
    assert result == "Logger 'tests.test_config' configured with level=DEBUG"


def test_configure_sentry_no_env_variable(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    result = configure_sentry()
    assert result == "No Sentry DSN found, exceptions will not be sent to Sentry"


def test_configure_sentry_env_variable_is_none(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "None")
    result = configure_sentry()
    assert result == "No Sentry DSN found, exceptions will not be sent to Sentry"


def test_configure_sentry_env_variable_is_dsn(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "https://1234567890@00000.ingest.sentry.io/123456")
    result = configure_sentry()
    assert result == "Sentry DSN found, exceptions will be sent to Sentry with env=test"


def test_load_config_values_success():
    config_values = load_config_values()
    assert config_values == {
        "FEED_TYPE": "test_feed_type",
        "LOG_LEVEL": "INFO",
        "SENTRY_DSN": "test_sentry_dsn",
        "SNS_TOPIC": "test_sns_topic",
        "WORKSPACE": "test",
        "CONNECTION_STRING": "sqlite://",
        "SYMPLECTIC_FTP_PATH": "/people.xml",
        "SYMPLECTIC_FTP_HOST": "localhost",
        "SYMPLECTIC_FTP_PORT": "test_symplectic_ftp_port",
        "SYMPLECTIC_FTP_USER": "user",
        "SYMPLECTIC_FTP_PASS": "pass",
    }
