# -*- coding: utf-8 -*-
from __future__ import absolute_import
from contextlib import contextmanager, closing
from datetime import datetime
from functools import partial
import re

from lxml import etree as ET
from sqlalchemy import func, select

from carbon.db import persons, orcids, dlcs, engine, aa_articles

AREAS = (
    'ARCHITECTURE & PLANNING AREA', 'ENGINEERING AREA',
    'HUMANITIES, ARTS, & SOCIAL SCIENCES AREA', 'SCIENCE AREA',
    'SLOAN SCHOOL OF MANAGEMENT AREA', 'VP RESEARCH',
)
PS_CODES = ('CFAN', 'CFAT', 'CFEL', 'CSRS', 'CSRR', 'COAC', 'COAR',)
TITLES = (
    'ADJUNCT ASSOCIATE PROFESSOR', 'ADJUNCT PROFESSOR', 'AFFILIATED ARTIST',
    'ASSISTANT PROFESSOR', 'ASSOCIATE PROFESSOR', 'ASSOCIATE PROFESSOR (NOTT)',
    'ASSOCIATE PROFESSOR (WOT)', 'ASSOCIATE PROFESSOR OF THE PRACTICE',
    'INSTITUTE OFFICIAL - EMERITUS', 'INSTITUTE PROFESSOR (WOT)',
    'INSTITUTE PROFESSOR EMERITUS', 'INSTRUCTOR', 'LECTURER', 'LECTURER II',
    'POSTDOCTORAL ASSOCIATE', 'POSTDOCTORAL FELLOW',
    'PRINCIPAL RESEARCH ASSOCIATE', 'PRINCIPAL RESEARCH ENGINEER',
    'PRINCIPAL RESEARCH SCIENTIST', 'PROFESSOR', 'PROFESSOR (NOTT)',
    'PROFESSOR (WOT)', 'PROFESSOR EMERITUS', 'PROFESSOR OF THE PRACTICE',
    'RESEARCH ASSOCIATE', 'RESEARCH ENGINEER',
    'RESEARCH FELLOW', 'RESEARCH SCIENTIST', 'RESEARCH SPECIALIST',
    'SENIOR LECTURER', 'SENIOR POSTDOCTORAL ASSOCIATE',
    'SENIOR POSTDOCTORAL FELLOW', 'SENIOR RESEARCH ASSOCIATE',
    'SENIOR RESEARCH ENGINEER', 'SENIOR RESEARCH SCIENTIST',
    'SENIOR RESEARCH SCIENTIST (MAP)', 'SPONSORED RESEARCH TECHNICAL STAFF',
    'SPONSORED RESEARCH TECHNICAL SUPERVISOR', 'STAFF AFFILIATE',
    'TECHNICAL ASSISTANT', 'TECHNICAL ASSOCIATE',
    'VISITING ASSISTANT PROFESSOR', 'VISITING ASSOCIATE PROFESSOR',
    'VISITING ENGINEER', 'VISITING LECTURER', 'VISITING PROFESSOR',
    'VISITING RESEARCH ASSOCIATE', 'VISITING SCHOLAR', 'VISITING SCIENTIST',
    'VISITING SENIOR LECTURER',
)


def people():
    """A person generator.

    Returns an iterator of person dictionaries.
    """
    sql = select([persons.c.MIT_ID, persons.c.KRB_NAME_UPPERCASE,
                  persons.c.FIRST_NAME, persons.c.MIDDLE_NAME,
                  persons.c.LAST_NAME, persons.c.EMAIL_ADDRESS,
                  persons.c.ORIGINAL_HIRE_DATE, dlcs.c.DLC_NAME,
                  persons.c.PERSONNEL_SUBAREA_CODE, orcids.c.ORCID]) \
        .select_from(persons.outerjoin(orcids).join(dlcs)) \
        .where(persons.c.EMAIL_ADDRESS != None) \
        .where(persons.c.LAST_NAME != None) \
        .where(persons.c.KRB_NAME_UPPERCASE != None) \
        .where(persons.c.KRB_NAME_UPPERCASE != 'UNKNOWN') \
        .where(persons.c.MIT_ID != None) \
        .where(persons.c.APPOINTMENT_END_DATE >= datetime(2009, 1, 1)) \
        .where(func.upper(dlcs.c.ORG_HIER_SCHOOL_AREA_NAME).in_(AREAS)) \
        .where(persons.c.PERSONNEL_SUBAREA_CODE.in_(PS_CODES)) \
        .where(func.upper(persons.c.JOB_TITLE).in_(TITLES))
    with closing(engine().connect()) as conn:
        for row in conn.execute(sql):
            yield dict(zip(row.keys(), row))


def articles():
    """An article generator.

    Returns an iterator over the AA_ARTICLE table.
    """
    sql = select([aa_articles])
    with closing(engine().connect()) as conn:
        for row in conn.execute(sql):
            yield dict(zip(row.keys(), row))


def initials(*args):
    """Turn `*args` into a space-separated string of initials.

    Each argument is processed through :func:`~initialize_part` and
    the resulting list is joined with a space.
    """
    return ' '.join([initialize_part(n) for n in args if n])


def initialize_part(name):
    """Turn a name part into uppercased initials.

    This function will do its best to parse the argument into one or
    more initials. The first step is to remove any character that is
    not alphanumeric, whitespace or a hyphen. The remaining string
    is split on word boundaries, retaining both the words and the
    boundaries. The first character of each list member is then
    joined together, uppercased and returned.

    Some examples::

        assert initialize_part('Foo Bar') == 'F B'
        assert initialize_part('F. Bar-Baz') == 'F B-B'
        assert initialize_part('Foo-bar') == 'F-B'
        assert initialize_part(u'влад') == u'В'

    """
    name = re.sub('[^\w\s-]', '', name, flags=re.UNICODE)
    return ''.join([x[:1] for x in re.split('(\W+)', name, flags=re.UNICODE)])\
        .upper()


def _ns(namespace, element):
    return ET.QName(namespace, element)


SYMPLECTIC_NS = 'http://www.symplectic.co.uk/hrimporter'
NSMAP = {None: SYMPLECTIC_NS}
ns = partial(_ns, SYMPLECTIC_NS)


def add_child(parent, element, text, **kwargs):
    """Add a subelement with text."""
    child = ET.SubElement(parent, element, attrib=kwargs)
    child.text = text
    return child


@contextmanager
def person_feed(out):
    """Generate XML feed of people.

    This is a streaming XML generator for people. Output will be
    written to the provided output destination which can be a file
    or file-like object. The context manager returns a function
    which can be called repeatedly to add a person to the feed::

        with person_feed(sys.stdout) as f:
            f({"MIT_ID": "1234", ...})
            f({"MIT_ID": "5678", ...})

    """
    with ET.xmlfile(out, encoding='UTF-8') as xf:
        xf.write_declaration()
        with xf.element(ns('records'), nsmap=NSMAP):
            yield partial(_add_person, xf)


@contextmanager
def article_feed(out):
    """Generate XML feed of articles."""
    with ET.xmlfile(out, encoding='UTF-8') as xf:
        xf.write_declaration()
        with xf.element('ARTICLES'):
            yield partial(_add_article, xf)


def _add_article(xf, article):
    record = ET.Element('ARTICLE')
    add_child(record, 'AA_MATCH_SCORE', str(article['AA_MATCH_SCORE']))
    add_child(record, 'ARTICLE_ID', article['ARTICLE_ID'])
    add_child(record, 'ARTICLE_TITLE', article['ARTICLE_TITLE'])
    add_child(record, 'ARTICLE_YEAR', article['ARTICLE_YEAR'])
    add_child(record, 'AUTHORS', article['AUTHORS'])
    add_child(record, 'DOI', article['DOI'])
    add_child(record, 'ISSN_ELECTRONIC', article['ISSN_ELECTRONIC'])
    add_child(record, 'ISSN_PRINT', article['ISSN_PRINT'])
    add_child(record, 'IS_CONFERENCE_PROCEEDING',
              article['IS_CONFERENCE_PROCEEDING'])
    add_child(record, 'JOURNAL_FIRST_PAGE', article['JOURNAL_FIRST_PAGE'])
    add_child(record, 'JOURNAL_LAST_PAGE', article['JOURNAL_LAST_PAGE'])
    add_child(record, 'JOURNAL_ISSUE', article['JOURNAL_ISSUE'])
    add_child(record, 'JOURNAL_VOLUME', article['JOURNAL_VOLUME'])
    add_child(record, 'JOURNAL_NAME', article['JOURNAL_NAME'])
    add_child(record, 'MIT_ID', article['MIT_ID'])
    add_child(record, 'PUBLISHER', article['PUBLISHER'])
    xf.write(record)


def _add_person(xf, person):
    record = ET.Element('record')
    add_child(record, 'field', person['MIT_ID'], name='[Proprietary_ID]')
    add_child(record, 'field', person['KRB_NAME_UPPERCASE'], name='[Username]')
    add_child(record, 'field', initials(person['FIRST_NAME'],
                                        person['MIDDLE_NAME']),
              name='[Initials]')
    add_child(record, 'field', person['LAST_NAME'], name='[LastName]')
    add_child(record, 'field', person['FIRST_NAME'], name='[FirstName]')
    add_child(record, 'field', person['EMAIL_ADDRESS'], name='[Email]')
    add_child(record, 'field', 'MIT', name='[AuthenticatingAuthority]')
    add_child(record, 'field', '1', name='[IsAcademic]')
    add_child(record, 'field', '1', name='[IsCurrent]')
    add_child(record, 'field', '1', name='[LoginAllowed]')
    add_child(record, 'field', person['DLC_NAME'],
              name='[PrimaryGroupDescriptor]')
    add_child(record, 'field', person['ORCID'], name='[Generic01]')
    add_child(record, 'field', person['PERSONNEL_SUBAREA_CODE'],
              name='[Generic02]')
    add_child(record, 'field',
              person['ORIGINAL_HIRE_DATE'].strftime("%Y-%m-%d"),
              name='[ArriveDate]')
    xf.write(record)
