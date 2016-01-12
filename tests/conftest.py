# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
import os

from lxml.builder import ElementMaker
import pytest

from carbon.db import engine, session, metadata, persons


@pytest.fixture(scope="session", autouse=True)
def app_init():
    engine.configure('sqlite://')
    metadata.bind = engine()
    metadata.create_all()


@pytest.fixture(scope="session")
def records():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    data = os.path.join(current_dir, 'fixtures/data.json')
    with open(data) as fp:
        r = json.load(fp)
    return r


@pytest.yield_fixture
def load_data(records):
    with session() as s:
        s.execute(persons.delete())
        s.execute(persons.insert(), records)
    yield
    with session() as s:
        s.execute(persons.delete())


@pytest.fixture
def xml_records(E):
    return [
        E.record(
            E.field('123456', {'name': '[Proprietary_ID]'}),
            E.field('foobar', {'name': '[Username]'}),
            E.field('F B', {'name': '[Initials]'}),
            E.field('Gaz', {'name': '[Lastname]'}),
            E.field('foobar@example.com', {'name': '[Email]'})
        ),
        E.record(
            E.field('098754', name='[Proprietary_ID]'),
            E.field('thor', name='[Username]'),
            E.field(u'Þ H', name='[Initials]'),
            E.field('Hammerson', name='[Lastname]'),
            E.field('thor@example.com', name='[Email]')
        )
    ]


@pytest.fixture
def xml_data(E, xml_records):
    return E.records(*xml_records)


@pytest.fixture
def E():
    return ElementMaker(namespace='http://www.symplectic.co.uk/hrimporter',
                        nsmap={None: 'http://www.symplectic.co.uk/hrimporter'})
