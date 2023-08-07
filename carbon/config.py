import json
import os

import sentry_sdk

ENV_VARS = [
    "FEED_TYPE",
    "LOG_LEVEL",
    "SENTRY_DSN",
    "SNS_TOPIC",
    "SYMPLECTIC_FTP_PATH",
    "WORKSPACE",
    "DATAWAREHOUSE_CLOUDCONNECTOR_JSON",
    "SYMPLECTIC_FTP_JSON",
]


def configure_sentry() -> str:
    """Establish Carbon project on Sentry.

    Returns:
        str: Status on whether Sentry was successfully configured.
    """
    env = os.getenv("WORKSPACE")
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn and sentry_dsn.lower() != "none":
        sentry_sdk.init(sentry_dsn, environment=env)
        return f"Sentry DSN found, exceptions will be sent to Sentry with env={env}"
    return "No Sentry DSN found, exceptions will not be sent to Sentry"


def load_config_values() -> dict:
    """Load required ENV variables into a 'config_values' dictionary.

    Returns:
        dict: Required ENV variables.
    """
    config_values = {}
    for config_variable in ENV_VARS:
        if config_variable in [
            "DATAWAREHOUSE_CLOUDCONNECTOR_JSON",
            "SYMPLECTIC_FTP_JSON",
        ]:
            config_values.update(json.loads(os.environ[config_variable]))
        config_values[config_variable] = os.environ[config_variable]

    return config_values
