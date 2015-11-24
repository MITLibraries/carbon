# -*- coding: utf-8 -*-
from __future__ import absolute_import

import click
import requests

from carbon import engine, people, PersonFeed


@click.group()
def main():
    pass


@main.command()
@click.option('--db', default='sqlite:///carbon.db')
@click.option('--url')
def load(db, url):
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
