import json
import logging
import os
from collections.abc import Iterable

import sentry_sdk

root_logger = logging.getLogger()


class Config:
    REQUIRED_ENVIRONMENT_VARIABLES: Iterable[str] = (
        "FEED_TYPE",
        "DATAWAREHOUSE_CLOUDCONNECTOR_JSON",
        "SYMPLECTIC_FTP_JSON",
        "SYMPLECTIC_FTP_PATH",
        "SNS_TOPIC_ARN",
        "WORKSPACE",
    )
    FEED_TYPE: str
    CONNECTION_STRING: str
    SYMPLECTIC_FTP_USER: str
    SYMPLECTIC_FTP_PASS: str
    SYMPLECTIC_FTP_HOST: str
    SYMPLECTIC_FTP_PORT: str
    SYMPLECTIC_FTP_PATH: str
    SNS_TOPIC_ARN: str
    WORKSPACE: str

    def __init__(
        self,
        log_level: str = "INFO",
    ) -> None:
        self.log_level = log_level

        self.configure_logger()
        self.load_environment_variables()
        self.configure_sentry()

    def configure_logger(self) -> None:
        """Configure logger."""
        try:
            log_level_code = getattr(logging, self.log_level.strip().upper())
        except AttributeError as error:
            msg = f"'{self.log_level}' is not a valid Python logging level"
            raise ValueError(msg) from error

        if log_level_code < logging.INFO:
            logging.basicConfig(
                format="%(asctime)s %(levelname)s %(name)s.%(funcName)s() "
                "line %(lineno)d: %(message)s"
            )
        else:
            logging.basicConfig(
                format="%(asctime)s %(levelname)s %(name)s.%(funcName)s(): %(message)s"
            )

        root_logger.setLevel(log_level_code)
        root_logger.info(
            "Logger '%s' configured with level=%s",
            root_logger.name,
            logging.getLevelName(root_logger.getEffectiveLevel()),
        )

    def configure_sentry(self) -> None:
        """Establish Carbon project on Sentry."""
        sentry_dsn = os.getenv("SENTRY_DSN", "None")
        if sentry_dsn and sentry_dsn.lower() != "none":
            sentry_sdk.init(sentry_dsn, environment=self.WORKSPACE)
            root_logger.info(
                "Sentry DSN found, exceptions will be sent to Sentry with env=%s",
                self.WORKSPACE,
            )
        else:
            root_logger.info("No Sentry DSN found, exceptions will not be sent to Sentry")

    def load_environment_variables(self) -> None:
        """Retrieve required environment variables and populate instance attributes."""
        for config_variable in self.REQUIRED_ENVIRONMENT_VARIABLES:
            try:
                if config_variable in [
                    "DATAWAREHOUSE_CLOUDCONNECTOR_JSON",
                    "SYMPLECTIC_FTP_JSON",
                ]:
                    for nested_config_variable, nested_config_value in json.loads(
                        os.environ[config_variable]
                    ).items():
                        setattr(self, nested_config_variable, nested_config_value)
                else:
                    setattr(self, config_variable, os.environ[config_variable])
            except KeyError:
                root_logger.exception(
                    "Config error: env variable '%s' is required, please set it.",
                    config_variable,
                )
                raise
