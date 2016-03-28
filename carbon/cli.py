# -*- coding: utf-8 -*-
from __future__ import absolute_import

import click

from carbon import people, person_feed
from carbon.db import engine


@click.group()
@click.version_option()
@click.argument('db')
def main(db):
    """Generate feeds for Symplectic Elements.

    The data is pulled from a database identified by DB, which should
    be a valid SQLAlchemy database connection string. For oracle use:

    oracle://<username>:<password>@<server>:1521/<sid>

    The feed will be printed to stdout.

    See the subcommands for specific feed information.
    """
    engine.configure(db)


@main.command()
def hr():
    """Generate a feed of people data."""
    out = click.get_binary_stream('stdout')
    with person_feed(out) as f:
        for person in people():
            f(person)
