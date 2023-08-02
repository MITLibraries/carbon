import os

import sentry_sdk


def configure_sentry() -> str:
    env = os.getenv("WORKSPACE")
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn and sentry_dsn.lower() != "none":
        sentry_sdk.init(sentry_dsn, environment=env)
        return (
            "Sentry DSN found, exceptions will be sent to Sentry "
            f"with env={env}"
        )
    return "No Sentry DSN found, exceptions will not be sent to Sentry"
