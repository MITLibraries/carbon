# -*- coding: utf-8 -*-
from __future__ import absolute_import

import click
import requests

from carbon import engine, people, PersonFeed


@click.group()
@click.version_option()
def main():
    pass


@main.command()
@click.argument('db')
@click.option('--url', help='URL for API endpoint')
def load(db, url):
    """Generate a feed of person data.

    The data is pulled from a database identified by DB, which should
    be a valid SQLAlchemy database connection string. The feed will
    be POSTed to URL if given, otherwise, it will be written to
    stdout.
    """
    engine.configure(db)
    feed = PersonFeed()
    for person in people():
        feed.add(person)
    if url is not None:
        headers = {'Content-type': 'application/xml; charset=UTF-8'}
        r = requests.post(url, data=feed.bytes(), headers=headers)
        r.raise_for_status()
    else:
        click.echo(feed.bytes())
