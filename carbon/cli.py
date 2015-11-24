# -*- coding: utf-8 -*-
from __future__ import absolute_import

import click

from carbon import engine, people, PersonFeed


@click.group()
def main():
    pass


@main.command()
@click.option('--db', default='sqlite:///carbon.db')
def load(db):
    engine.configure(db)
    feed = PersonFeed()
    for person in people():
        feed.add(person)
    click.echo(feed.bytes())
