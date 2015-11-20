# -*- coding: utf-8 -*-
from __future__ import absolute_import

import click

from carbon.db import engine, session


@click.group()
def main():
    pass


@main.command()
@click.option('--db', default='sqlite:///carbon.db')
def load(db):
    engine.configure(db)
    with session() as s:
        pass
