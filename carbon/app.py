# -*- coding: utf-8 -*-
from __future__ import absolute_import
from contextlib import contextmanager, closing
from datetime import datetime
from functools import partial
import ftplib
import os
import re
import threading

from lxml import etree as ET
from sqlalchemy import func, select

from carbon.db import persons, orcids, dlcs, engine, aa_articles

AREAS = (
    'ARCHITECTURE & PLANNING AREA', 'ENGINEERING AREA',
    'HUMANITIES, ARTS, & SOCIAL SCIENCES AREA', 'SCIENCE AREA',
    'SLOAN SCHOOL OF MANAGEMENT AREA', 'VP RESEARCH', 'CHANCELLOR\'S AREA',
    'OFFICE OF PROVOST AREA', 'PROVOST AREA',
)
PS_CODES = ('CFAN', 'CFAT', 'CFEL', 'CSRS', 'CSRR', 'COAC', 'COAR', 'L303',)
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
    'VISITING SENIOR LECTURER', 'PART-TIME FLEXIBLE/LL',
)


def people():
    """A person generator.

    Returns an iterator of person dictionaries.
    """
    sql = select([persons.c.MIT_ID, persons.c.KRB_NAME_UPPERCASE,
                  persons.c.FIRST_NAME, persons.c.MIDDLE_NAME,
                  persons.c.LAST_NAME, persons.c.EMAIL_ADDRESS,
                  persons.c.ORIGINAL_HIRE_DATE, dlcs.c.DLC_NAME,
                  persons.c.PERSONNEL_SUBAREA_CODE,
                  persons.c.APPOINTMENT_END_DATE, orcids.c.ORCID,
                  dlcs.c.ORG_HIER_SCHOOL_AREA_NAME,
                  dlcs.c.HR_ORG_LEVEL5_NAME,]) \
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
    sql = select([aa_articles]) \
        .where(aa_articles.c.ARTICLE_ID != None) \
        .where(aa_articles.c.ARTICLE_TITLE != None) \
        .where(aa_articles.c.DOI != None) \
        .where(aa_articles.c.MIT_ID != None)
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


def group_name(dlc, sub_area):
    qualifier = 'Faculty' if sub_area in ('CFAT', 'CFAN') else 'Non-faculty'
    return "{} {}".format(dlc, qualifier)

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


class Writer:
    """A Symplectic Elements feed writer.

    Use this class to generate and output an HR or AA feed for Symplectic
    Elements.
    """
    def __init__(self, out):
        self.out = out

    def write(self, feed_type):
        """Write the specified feed type to the configured output."""
        if feed_type == 'people':
            with person_feed(self.out) as f:
                for person in people():
                    f(person)
        elif feed_type == 'articles':
            with article_feed(self.out) as f:
                for article in articles():
                    f(article)


class PipeWriter(Writer):
    """A read/write :class:`carbon.app.Writer`.

    This class is intended to provide a buffered read/write connecter. The
    :meth:`~carbon.app.PipeWriter.pipe` method should be called before
    writing to configure the reader end. For example::

        PipeWriter(fp_out).pipe(reader).write('people')

    See :class:`carbon.app.FTPReader` for an example reader.
    """
    def write(self, feed_type):
        """Concurrently read/write from the configured inputs and outputs.

        This method will block until both the reader and writer are finished.
        """
        pipe = threading.Thread(target=self._reader)
        pipe.start()
        super().write(feed_type)
        self.out.close()
        pipe.join()

    def pipe(self, reader):
        """Connect the read end of the pipe.

        This should be called before :meth:`~carbon.app.PipeWriter.write`.
        """
        self._reader = reader
        return self


class FTPReader:
    def __init__(self, fp, user, passwd, path, host='localhost', port=21):
        self.fp = fp
        self.user = user
        self.passwd = passwd
        self.path = path
        self.host = host
        self.port = port

    def __call__(self):
        """Transfer a file using FTP over TLS."""
        ftps = ftplib.FTP_TLS()
        ftps.connect(self.host, self.port)
        ftps.login(self.user, self.passwd)
        ftps.prot_p()
        ftps.storbinary("STOR " + self.path, self.fp)
        ftps.quit()


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
    add_child(record, 'field',
              group_name(person['DLC_NAME'], person['PERSONNEL_SUBAREA_CODE']),
              name='[PrimaryGroupDescriptor]')
    add_child(record, 'field',
              person['ORIGINAL_HIRE_DATE'].strftime("%Y-%m-%d"),
              name='[ArriveDate]')
    add_child(record, 'field',
              person['APPOINTMENT_END_DATE'].strftime("%Y-%m-%d"),
              name='[LeaveDate]')
    add_child(record, 'field', person['ORCID'], name='[Generic01]')
    add_child(record, 'field', person['PERSONNEL_SUBAREA_CODE'],
              name='[Generic02]')
    add_child(record, 'field', person['ORG_HIER_SCHOOL_AREA_NAME'],
              name='[Generic03]')
    add_child(record, 'field', person['DLC_NAME'], name='[Generic04]')
    add_child(record, 'field', person.get('HR_ORG_LEVEL5_NAME'),
              name='[Generic05]')
    xf.write(record)


class Config(dict):
    @classmethod
    def from_env(cls):
        cfg = cls()
        for var in ['FTP_USER', 'FTP_PASS', 'FTP_PATH', 'FTP_HOST',
                    'CARBON_DB',]:
            cfg[var] = os.environ.get(var)
        return cfg


class FTPFeeder:
    def __init__(self, event, context, config):
        self.event = event
        self.context = context
        self.config = config

    def run(self):
        r, w = os.pipe()
        feed_type = self.event['feed_type']
        with open(r, 'rb') as fp_r, open(w, 'wb') as fp_w:
            ftp_rdr = FTPReader(fp_r,
                                self.config['FTP_USER'],
                                self.config['FTP_PASS'],
                                self.config['FTP_PATH'],
                                self.config['FTP_HOST'],
                                self.config['FTP_PORT'])
            PipeWriter(out=fp_w).pipe(ftp_rdr).write(feed_type)
