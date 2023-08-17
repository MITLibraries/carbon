import logging
import os

import click

from carbon.app import FTPFeeder, sns_log
from carbon.config import configure_logger, load_config_values  # configure_sentry
from carbon.db import engine

logger = logging.getLogger(__name__)


@click.command()
@click.version_option()
def main() -> None:
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
    sns_log(config_values=config_values, status="start")

    try:
        root_logger = logging.getLogger()
        logger.info(configure_logger(root_logger, os.getenv("LOG_LEVEL", "INFO")))
        # configure_sentry() # noqa: ERA001
        logger.info(
            "Carbon config settings loaded for environment: %s",
            config_values["WORKSPACE"],
        )

        engine.configure(config_values["CONNECTION_STRING"])

        click.echo("Starting carbon run for {}".format(config_values["FEED_TYPE"]))
        FTPFeeder({"feed_type": config_values["FEED_TYPE"]}, config_values).run()
        click.echo("Finished carbon run for {}".format(config_values["FEED_TYPE"]))
    except RuntimeError:
        sns_log(config_values=config_values, status="fail")
    else:
        sns_log(config_values=config_values, status="success")
