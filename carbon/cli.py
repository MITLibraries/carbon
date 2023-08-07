import json
import os
from typing import IO

import click

from carbon.app import FTPFeeder, Writer, sns_log
from carbon.config import configure_logger, configure_sentry, load_config_values
from carbon.db import engine


@click.command()
@click.version_option()
@click.argument(
    "feed_type", envvar="FEED_TYPE", type=click.Choice(["people", "articles"])
)
@click.option("--db", envvar="CONNECTION_STRING", help="Database connection string")
@click.option("-o", "--out", help="Output file", type=click.File("wb"))
@click.option(
    "--ftp",
    is_flag=True,
    help="Send output to FTP server; do not use this with the -o/--out option",
)
@click.option(
    "--ftp-host",
    envvar="SYMPLECTIC_FTP_HOST",
    help="Hostname of FTP server",
    default="localhost",
    show_default=True,
)
@click.option(
    "--ftp-port",
    envvar="SYMPLECTIC_FTP_PORT",
    help="FTP server port",
    default=21,
    show_default=True,
)
@click.option("--ftp-user", envvar="SYMPLECTIC_FTP_USER", help="FTP username")
@click.option("--ftp-pass", envvar="SYMPLECTIC_FTP_PASS", help="FTP password")
@click.option(
    "--ftp-path", envvar="SYMPLECTIC_FTP_PATH", help="Full path to file on FTP server"
)
@click.option(
    "--secret-id",
    help="AWS Secrets id containing DB connection "
    "string and FTP password. If given, will "
    "override other command line options.",
)
@click.option(
    "--sns-topic",
    help="AWS SNS Topic ARN. If given, a message "
    "will be sent when the load begins and "
    "then another message will be sent with "
    "the outcome of the load.",
)
@sns_log
def main(
    feed_type: str,
    db: str,
    out: IO,
    ftp_host: str,
    ftp_port: int,
    ftp_user: str,
    ftp_pass: str,
    ftp_path: str,
    secret_id: str,
    sns_topic: str,  # noqa: ARG001
    *,
    ftp: bool,
) -> None:
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

    # [TEMPORARY] In order to pass the current test, config_values
    #   must be updated with any arguments set when the function is
    #   invoked.
    # Note: For FTP port, the default value is 21, but we currently do not have
    #   an environment variable set. We may need to create an environment variable
    #   SYMPLECTIC_FTP_PORT for consistency.
    config_values.update(
        {
            "CONNECTION_STRING": db,
            "SYMPLECTIC_FTP_USER": ftp_user,
            "SYMPLECTIC_FTP_PASS": ftp_pass,
            "SYMPLECTIC_FTP_PATH": ftp_path,
            "SYMPLECTIC_FTP_HOST": ftp_host,
            "SYMPLECTIC_FTP_PORT": ftp_port,
        }
    )

    # configure_sentry()

    engine.configure(config_values["CONNECTION_STRING"])
    if ftp:
        click.echo("Starting carbon run for {}".format(feed_type))
        FTPFeeder({"feed_type": feed_type}, None, config_values).run()
        click.echo("Finished carbon run for {}".format(feed_type))
    else:
        Writer(out=out).write(feed_type)
