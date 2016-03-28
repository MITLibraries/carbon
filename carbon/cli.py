# -*- coding: utf-8 -*-
from __future__ import absolute_import

import click

from carbon import people, person_feed
from carbon.db import engine


@click.group()
@click.version_option()
def main():
    pass


@main.command()
@click.argument('db')
@click.option('-o', '--out', help='Output file',
              default=click.get_binary_stream('stdout'))
def feed(db, out):
    """Generate a feed of person data.

    The data is pulled from a database identified by DB, which should
    be a valid SQLAlchemy database connection string. The feed will be
    printed to stdout unless a destination file is specified by OUT.
    """
    engine.configure(db)
    with person_feed(out) as f:
        for person in people():
            f(person)
