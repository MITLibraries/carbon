# -*- coding: utf-8 -*-
from __future__ import absolute_import
from contextlib import closing
import os

from lxml.builder import ElementMaker, E as B
import pytest
import yaml

from carbon.db import engine, metadata, persons, orcids, dlcs, aa_articles


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


@pytest.fixture(scope="session")
def aa_data():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    data = os.path.join(current_dir, 'fixtures/articles.yml')
    with open(data) as fp:
        r = list(yaml.load_all(fp))
    return r


@pytest.yield_fixture
def load_data(records, aa_data):
    with closing(engine().connect()) as conn:
        conn.execute(persons.delete())
        conn.execute(orcids.delete())
        conn.execute(dlcs.delete())
        conn.execute(aa_articles.delete())
        for r in records:
            conn.execute(persons.insert(), r['person'])
            conn.execute(orcids.insert(), r['orcid'])
            conn.execute(dlcs.insert(), r['dlc'])
        conn.execute(aa_articles.insert(), aa_data)
    yield
    with closing(engine().connect()) as conn:
        conn.execute(persons.delete())
        conn.execute(orcids.delete())
        conn.execute(dlcs.delete())
        conn.execute(aa_articles.delete())


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
            E.field('Chemistry Faculty', {'name': '[PrimaryGroupDescriptor]'}),
            E.field('2001-01-01', {'name': '[ArriveDate]'}),
            E.field('http://example.com/1', {'name': '[Generic01]'}),
            E.field('CFAT', {'name': '[Generic02]'}),
            E.field('SCIENCE AREA', {'name': '[Generic03]'}),
            E.field('Chemistry', {'name': '[Generic04]'}),
            E.field(name='[Generic05]')
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
            E.field('Nuclear Science Non-faculty',
                    {'name': '[PrimaryGroupDescriptor]'}),
            E.field('2015-01-01', {'name': '[ArriveDate]'}),
            E.field('http://example.com/2', {'name': '[Generic01]'}),
            E.field('COAC', {'name': '[Generic02]'}),
            E.field('ENGINEERING AREA', {'name': '[Generic03]'}),
            E.field('Nuclear Science', {'name': '[Generic04]'}),
            E.field('Nuclear Science and Engineering', {'name': '[Generic05]'})
        )
    ]


@pytest.fixture
def xml_data(E, xml_records):
    return E.records(*xml_records)


@pytest.fixture
def E():
    return ElementMaker(namespace='http://www.symplectic.co.uk/hrimporter',
                        nsmap={None: 'http://www.symplectic.co.uk/hrimporter'})


@pytest.fixture
def articles_data(aa_data):
    return B.ARTICLES(
        B.ARTICLE(
            B.AA_MATCH_SCORE('0.9'),
            B.ARTICLE_ID('1234567'),
            B.ARTICLE_TITLE(u'Interaction between hatsopoulos microfluids and the Yawning Abyss of Chaos ☈.'),
            B.ARTICLE_YEAR('1999'),
            B.AUTHORS(u'McRandallson, Randall M.|Lord, Dark|☭'),
            B.DOI('10.0000/1234LETTERS56'),
            B.ISSN_ELECTRONIC('0987654'),
            B.ISSN_PRINT('01234567'),
            B.IS_CONFERENCE_PROCEEDING('0'),
            B.JOURNAL_FIRST_PAGE('666'),
            B.JOURNAL_LAST_PAGE('666'),
            B.JOURNAL_ISSUE('10'),
            B.JOURNAL_VOLUME('1'),
            B.JOURNAL_NAME('Bunnies'),
            B.MIT_ID('123456789'),
            B.PUBLISHER('MIT Press')
            )
        )
