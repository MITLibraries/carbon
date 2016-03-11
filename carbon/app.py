# -*- coding: utf-8 -*-
from __future__ import absolute_import
from contextlib import contextmanager, closing
from datetime import datetime
from functools import partial
import re

from lxml import etree as ET
from sqlalchemy import func, select, and_, or_

from carbon.db import persons, orcids, engine


PS_CODES_1 = ('CFAC', 'CFAN', 'CFAT', 'CFEL', 'CSRS', 'CSRR')
PS_CODES_2 = ('COAC', 'COAR')
TITLES = (
    'ADJUNCT ASSOCIATE PROFESSOR', 'ADJUNCT PROFESSOR',
    'ASSOCIATE PROFESSOR OF THE PRACTICE', 'INSTITUTE PROFESSOR (WOT)',
    'INSTITUTE PROFESSOR EMERITUS', 'INSTRUCTOR', 'LECTURER', 'LECTURER II',
    'PROFESSOR (WOT)', 'PROFESSOR EMERITUS', 'SENIOR LECTURER',
    'VISITING ASSISTANT PROFESSOR', 'VISITING ASSOCIATE PROFESSOR',
    'VISITING PROFESSOR', 'VISITING SCHOLAR', 'VISITING SCIENTIST',
    'POSTDOCTORAL ASSOCIATE', 'POSTDOCTORAL FELLOW',
    'SENIOR POSTDOCTORAL ASSOCIATE', 'VISITING ENGINEER', 'VISITING SCHOLAR',
    'VISITING SCIENTIST',
)


def people():
    """A person generator.

    Returns an iterator of person dictionaries.
    """
    sql = select([persons.c.MIT_ID, persons.c.KRB_NAME_UPPERCASE,
                  persons.c.FIRST_NAME, persons.c.MIDDLE_NAME,
                  persons.c.LAST_NAME, persons.c.EMAIL_ADDRESS,
                  persons.c.ORIGINAL_HIRE_DATE, persons.c.HR_ORG_UNIT_TITLE,
                  persons.c.PERSONNEL_SUBAREA_CODE, orcids.c.ORCID]) \
        .select_from(persons.outerjoin(orcids)) \
        .where(persons.c.EMAIL_ADDRESS != None) \
        .where(persons.c.APPOINTMENT_END_DATE >= datetime(2009, 1, 1)) \
        .where(
            or_(
                persons.c.PERSONNEL_SUBAREA_CODE.in_(PS_CODES_1),
                and_(
                    persons.c.PERSONNEL_SUBAREA_CODE.in_(PS_CODES_2),
                    func.upper(persons.c.JOB_TITLE).in_(TITLES)
                )
            )
        )
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
    add_child(record, 'field', '0', name='[LoginAllowed]')
    add_child(record, 'field', person['HR_ORG_UNIT_TITLE'],
              name='[PrimaryGroupDescriptor]')
    add_child(record, 'field', person['ORCID'], name='[Generic01]')
    add_child(record, 'field', person['PERSONNEL_SUBAREA_CODE'],
              name='[Generic02]')
    add_child(record, 'field',
              person['ORIGINAL_HIRE_DATE'].strftime("%Y-%m-%d"),
              name='[ArriveDate]')
    xf.write(record)
