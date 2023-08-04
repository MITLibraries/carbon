# -*- coding: utf-8 -*-
from __future__ import absolute_import

import json

import boto3
import click

from carbon.app import Config, FTPFeeder, Writer, sns_log
from carbon.config import configure_sentry
from carbon.db import engine


@click.command()
@click.version_option()
@click.argument("feed_type", type=click.Choice(["people", "articles"]))
@click.option("--db", envvar="CARBON_DB", help="Database connection string")
@click.option("-o", "--out", help="Output file", type=click.File("wb"))
@click.option(
    "--ftp",
    is_flag=True,
    help="Send output to FTP server; do not " "use this with the -o/--out option",
)
@click.option(
    "--ftp-host",
    envvar="FTP_HOST",
    help="Hostname of FTP server",
    default="localhost",
    show_default=True,
)
@click.option(
    "--ftp-port",
    envvar="FTP_PORT",
    help="FTP server port",
    default=21,
    show_default=True,
)
@click.option("--ftp-user", envvar="FTP_USER", help="FTP username")
@click.option("--ftp-pass", envvar="FTP_PASS", help="FTP password")
@click.option("--ftp-path", envvar="FTP_PATH", help="Full path to file on FTP server")
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
    feed_type,
    db,
    out,
    ftp,
    ftp_host,
    ftp_port,
    ftp_user,
    ftp_pass,
    ftp_path,
    secret_id,
    sns_topic,
):
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
    cfg = Config(
        CARBON_DB=db,
        FTP_USER=ftp_user,
        FTP_PASS=ftp_pass,
        FTP_PATH=ftp_path,
        FTP_HOST=ftp_host,
        FTP_PORT=ftp_port,
    )
    configure_sentry()

    if secret_id is not None:
        client = boto3.client("secretsmanager")
        secret = client.get_secret_value(SecretId=secret_id)
        secret_env = json.loads(secret["SecretString"])
        cfg.update(secret_env)

    engine.configure(cfg["CARBON_DB"])
    if ftp:
        click.echo("Starting carbon run for {}".format(feed_type))
        FTPFeeder({"feed_type": feed_type}, None, cfg).run()
        click.echo("Finished carbon run for {}".format(feed_type))
    else:
        Writer(out=out).write(feed_type)
