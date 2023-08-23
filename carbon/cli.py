import logging
import os

import click

from carbon.app import FTPFeeder, sns_log
from carbon.config import configure_logger, configure_sentry, load_config_values
from carbon.db import engine

logger = logging.getLogger(__name__)


@click.command()
@click.version_option()
@click.option("--run_connection_tests", is_flag=True)
def main(*, run_connection_tests: bool) -> None:
    """Generate feeds for Symplectic Elements.

    Specify which FEED_TYPE should be generated. This should be either
    'people' or 'articles'.

    The data is pulled from a database identified by --db, which should
    be a valid SQLAlchemy database connection string. This can also be
    omitted and pulled from an environment variable named CARBON_DB. For
    oracle use:

    oracle://<username>:<password>@<server>:1521/<sid>

    By default, the feed will be printed to stdout. If -o/--out is used the
    output will be written to the specified file instead.

    Alternatively, the --ftp switch can be used to send the output to an FTP
    server. The server should support FTP over TLS. Only one of -o/--out or
    --ftp should be used.
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
    ftp_feed = FTPFeeder({"feed_type": config_values["FEED_TYPE"]}, config_values)
    ftp_feed.run_connection_test()

    if not run_connection_tests:
        sns_log(config_values=config_values, status="start")
        try:
            ftp_feed.run()
        except Exception as error:  # noqa: BLE001
            sns_log(config_values=config_values, status="fail", error=error)
        else:
            sns_log(config_values=config_values, status="success")
