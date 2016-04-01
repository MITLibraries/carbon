# -*- coding: utf-8 -*-
from __future__ import absolute_import
from contextlib import closing
import os

from lxml.builder import ElementMaker
import pytest
import yaml

from carbon.db import engine, metadata, persons, orcids, dlcs


@pytest.fixture(scope="session", autouse=True)
def app_init():
    engine.configure('sqlite://')
    metadata.bind = engine()
    metadata.create_all()


@pytest.fixture(scope="session")
def records():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    data = os.path.join(current_dir, 'fixtures/data.yml')
    with open(data) as fp:
        r = list(yaml.load_all(fp))
    return r


@pytest.yield_fixture
def load_data(records):
    with closing(engine().connect()) as conn:
        conn.execute(persons.delete())
        conn.execute(orcids.delete())
        conn.execute(dlcs.delete())
        for r in records:
            conn.execute(persons.insert(), r['person'])
            conn.execute(orcids.insert(), r['orcid'])
            conn.execute(dlcs.insert(), r['dlc'])
    yield
    with closing(engine().connect()) as conn:
        conn.execute(persons.delete())
        conn.execute(orcids.delete())
        conn.execute(dlcs.delete())


@pytest.fixture
def xml_records(E):
    return [
        E.record(
            E.field('123456', {'name': '[Proprietary_ID]'}),
            E.field('FOOBAR', {'name': '[Username]'}),
            E.field('F B', {'name': '[Initials]'}),
            E.field('Gaz', {'name': '[LastName]'}),
            E.field('Foobar', {'name': '[FirstName]'}),
            E.field('foobar@example.com', {'name': '[Email]'}),
            E.field('MIT', {'name': '[AuthenticatingAuthority]'}),
            E.field('1', {'name': '[IsAcademic]'}),
            E.field('1', {'name': '[IsCurrent]'}),
            E.field('1', {'name': '[LoginAllowed]'}),
            E.field('Chemistry', {'name': '[PrimaryGroupDescriptor]'}),
            E.field('http://example.com/1', {'name': '[Generic01]'}),
            E.field('CFAT', {'name': '[Generic02]'}),
            E.field('2001-01-01', {'name': '[ArriveDate]'})
        ),
        E.record(
            E.field('098754', name='[Proprietary_ID]'),
            E.field('THOR', name='[Username]'),
            E.field(u'Þ H', name='[Initials]'),
            E.field('Hammerson', name='[LastName]'),
            E.field(u'Þorgerðr', name='[FirstName]'),
            E.field('thor@example.com', name='[Email]'),
            E.field('MIT', {'name': '[AuthenticatingAuthority]'}),
            E.field('1', {'name': '[IsAcademic]'}),
            E.field('1', {'name': '[IsCurrent]'}),
            E.field('1', {'name': '[LoginAllowed]'}),
            E.field('Nuclear Science', {'name': '[PrimaryGroupDescriptor]'}),
            E.field('http://example.com/2', {'name': '[Generic01]'}),
            E.field('COAC', {'name': '[Generic02]'}),
            E.field('2015-01-01', {'name': '[ArriveDate]'})
        )
    ]


@pytest.fixture
def xml_data(E, xml_records):
    return E.records(*xml_records)


@pytest.fixture
def E():
    return ElementMaker(namespace='http://www.symplectic.co.uk/hrimporter',
                        nsmap={None: 'http://www.symplectic.co.uk/hrimporter'})
