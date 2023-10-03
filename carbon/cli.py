import logging
import os
from typing import IO

import click

from carbon.app import DatabaseToFilePipe, DatabaseToFtpPipe, run_all_connection_tests
from carbon.config import Config
from carbon.database import DatabaseEngine
from carbon.helpers import sns_log

root_logger = logging.getLogger()
logger = logging.getLogger(__name__)


@click.command()
@click.version_option()
@click.option(
    "-o",
    "--output_file",
    help=(
        "Name of file (including the extension) into which Carbon writes the output. "
        "Defaults to None, which will write the output to an XML file on the "
        "Symplectic Elements FTP server."
    ),
    type=click.File("wb"),
    default=None,
)
@click.option(
    "--run_connection_tests",
    help="Test connection to the Data Warehouse and the Symplectic Elements FTP server",
    is_flag=True,
)
@click.option(
    "--use_sns_logging/--ignore_sns_logging",
    help=(
        "Turn on SNS logging. If SNS logging is used, notification emails "
        "indicating the start and result of a Carbon run will be sent to subscribers "
        "for the Carbon topic. Defaults to True."
    ),
    default=True,
)
def main(*, output_file: IO, run_connection_tests: bool, use_sns_logging: bool) -> None:
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
    config = Config(log_level=os.getenv("LOG_LEVEL", "INFO"))

    # [TEMP]: The connection string must use 'oracle+oracledb' to differentiate
    # between the cx_Oracle and python-oracledb drivers
    config.CONNECTION_STRING = config.CONNECTION_STRING.replace(
        "oracle", "oracle+oracledb"
    )

    logger.info(
        "Carbon config settings loaded for environment: %s",
        config.WORKSPACE,
    )

    engine = DatabaseEngine()
    engine.configure(config.CONNECTION_STRING, thick_mode=True)

    pipe: DatabaseToFtpPipe | DatabaseToFilePipe
    if output_file:
        pipe = DatabaseToFilePipe(config=config, engine=engine, output_file=output_file)
    else:
        pipe = DatabaseToFtpPipe(config=config, engine=engine)

    run_all_connection_tests(engine=engine, pipe=pipe)

    if not run_connection_tests:
        logger.info("Carbon run for the '%s' feed has started.", config.FEED_TYPE)
        if use_sns_logging:
            sns_log(config=config, status="start")
        try:
            pipe.run()
        except Exception as error:  # noqa: BLE001
            logger.error("Carbon run has failed.")  # noqa: TRY400
            if use_sns_logging:
                sns_log(config=config, status="fail", error=error)
        else:
            logger.info("Carbon run has successfully completed.")
            if use_sns_logging:
                sns_log(config=config, status="success")
