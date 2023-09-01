import logging
import os

import click

from carbon.app import DatabaseToFtpPipe
from carbon.config import configure_logger, configure_sentry, load_config_values
from carbon.database import engine
from carbon.helpers import sns_log

logger = logging.getLogger(__name__)


@click.command()
@click.version_option()
@click.option("--run_connection_tests", is_flag=True)
def main(*, run_connection_tests: bool) -> None:
    """Generate a data feed that uploads XML files to the Symplectic Elements FTP server.

    The feed uses a SQLAlchemy engine to connect to the Data Warehouse. A query is
    submitted to the Data Warehouse to retrieve either 'people' or 'articles' records
    depending on the 'FEED_TYPE' environment variable. Several transforms are applied
    to normalize the records before it is converted to an XML string.
    The feed builds a pipe that will concurrently read data from the Data Warehouse
    and write the normalized XML string to an XML file on the Elements
    FTP server. For security purposes, the server should support FTP over TLS.

    [wip] By default, the feed will write to an XML file on the Elements FTP server.
    If the -o/--out argument is used, the output will be written to the specified
    file instead. This latter option is recommended for testing purposes.
    """
    config_values = load_config_values()
    # [TEMP]: The connection string must use 'oracle+oracledb' to differentiate
    # between the cx_Oracle and python-oracledb drivers
    config_values["CONNECTION_STRING"] = config_values["CONNECTION_STRING"].replace(
        "oracle", "oracle+oracledb"
    )
    root_logger = logging.getLogger()
    logger.info(configure_logger(root_logger, os.getenv("LOG_LEVEL", "INFO")))
    configure_sentry()
    logger.info(
        "Carbon config settings loaded for environment: %s",
        config_values["WORKSPACE"],
    )

    # test connection to the Data Warehouse
    engine.configure(config_values["CONNECTION_STRING"], thick_mode=True)
    engine.run_connection_test()

    # test connection to the Symplectic Elements FTP server
    pipe = DatabaseToFtpPipe(config=config_values)
    pipe.run_connection_test()

    if not run_connection_tests:
        sns_log(config_values=config_values, status="start")
        try:
            pipe.run()
        except Exception as error:  # noqa: BLE001
            sns_log(config_values=config_values, status="fail", error=error)
        else:
            sns_log(config_values=config_values, status="success")
