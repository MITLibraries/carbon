# -*- coding: utf-8 -*-
from __future__ import absolute_import

import click

from carbon import engine, people


@click.group()
def main():
    pass


@main.command()
@click.option('--db', default='sqlite:///carbon.db')
def load(db):
    engine.configure(db)
    for person in people():
        click.echo(person)
