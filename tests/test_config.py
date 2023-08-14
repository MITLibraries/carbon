from carbon.config import configure_sentry


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
