# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os

from sqlalchemy import (create_engine, Table, Column, String, Date, MetaData,
                        ForeignKey, Numeric, Unicode, UnicodeText)


os.environ['NLS_LANG'] = 'AMERICAN_AMERICA.UTF8'

metadata = MetaData()


persons = Table('HR_PERSON_EMPLOYEE_LIMITED', metadata,
                Column('MIT_ID', String),
                Column('KRB_NAME_UPPERCASE', String),
                Column('FIRST_NAME', Unicode),
                Column('LAST_NAME', Unicode),
                Column('MIDDLE_NAME', Unicode),
                Column('EMAIL_ADDRESS', String),
                Column('ORIGINAL_HIRE_DATE', Date),
                Column('APPOINTMENT_END_DATE', Date),
                Column('PERSONNEL_SUBAREA_CODE', String),
                Column('JOB_TITLE', String),
                Column('HR_ORG_UNIT_ID', String),
                )

dlcs = Table('HR_ORG_UNIT', metadata,
             Column('HR_ORG_UNIT_ID', String,
                    ForeignKey('HR_PERSON_EMPLOYEE_LIMITED.HR_ORG_UNIT_ID')),
             Column('ORG_HIER_SCHOOL_AREA_NAME', String),
             Column('DLC_NAME', String),
             Column('HR_ORG_LEVEL5_NAME', String),
             )


orcids = Table('ORCID_TO_MITID', metadata,
               Column('MIT_ID', String,
                      ForeignKey('HR_PERSON_EMPLOYEE_LIMITED.MIT_ID')),
               Column('ORCID', String))


aa_articles = Table('AA_ARTICLE', metadata,
                    Column('AA_MATCH_SCORE', Numeric(3, 1)),
                    Column('ARTICLE_ID', String),
                    Column('ARTICLE_TITLE', Unicode),
                    Column('ARTICLE_YEAR', String),
                    Column('AUTHORS', UnicodeText),
                    Column('DOI', String),
                    Column('ISSN_ELECTRONIC', String),
                    Column('ISSN_PRINT', String),
                    Column('IS_CONFERENCE_PROCEEDING', String),
                    Column('JOURNAL_FIRST_PAGE', String),
                    Column('JOURNAL_LAST_PAGE', String),
                    Column('JOURNAL_ISSUE', Unicode),
                    Column('JOURNAL_NAME', Unicode),
                    Column('JOURNAL_VOLUME', Unicode),
                    Column('MIT_ID', String),
                    Column('PUBLISHER', Unicode),
                    )


class Engine(object):
    """Database engine.

    This provides access to an SQLAlchemy database engine. Only one
    of these should be created per application. Calling the object
    will return the configured engine, though you should generally
    use the :func:`~carbon.db.session` to interact with the databse.
    """
    _engine = None

    def __call__(self):
        return self._engine

    def configure(self, conn):
        self._engine = self._engine or create_engine(conn)


engine = Engine()
"""Application database engine."""
