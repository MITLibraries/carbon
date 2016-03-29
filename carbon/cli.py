# -*- coding: utf-8 -*-
from __future__ import absolute_import

import click

from carbon import people, person_feed
from carbon.db import engine


@click.command()
@click.version_option()
@click.argument('db')
@click.argument('feed_type', type=click.Choice(['people', 'articles']))
@click.option('-o', '--out', help='Output file', type=click.File('wb'),
              default='-')
def main(db, feed_type, out):
    """Generate feeds for Symplectic Elements.

    The data is pulled from a database identified by DB, which should
    be a valid SQLAlchemy database connection string. For oracle use:

    oracle://<username>:<password>@<server>:1521/<sid>

    The feed will be printed to stdout if OUT is not specified.

    FEED_TYPE should be 'people'.
    """
    engine.configure(db)
    if feed_type == 'people':
        with person_feed(out) as f:
            for person in people():
                f(person)
