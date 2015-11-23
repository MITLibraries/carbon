# -*- coding: utf-8 -*-
from __future__ import absolute_import
from contextlib import contextmanager

from sqlalchemy import (create_engine, Table, Column, String, Date, MetaData,)


metadata = MetaData()


persons = Table('library_person_lookup', metadata,
                Column('MIT_ID', String),
                Column('KRB_NAME', String),
                Column('FIRST_NAME', String),
                Column('LAST_NAME', String),
                Column('EMAIL', String),
                Column('START_DATE', Date),
                Column('END_DATE', Date),
                Column('DEPARTMENT_NAME', String))


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


@contextmanager
def session():
    """Scoped session context for performing database operations.

    The database engine needs to be configured before using a
    session. For example::

        from carbon import engine, session

        engine.configure('sqlite:///:memory:')
        with session() as s:
            s.execute() ...
    """
    conn = engine().connect()
    tx = conn.begin()
    try:
        yield conn
        tx.commit()
    except:
        tx.rollback()
        raise
    finally:
        conn.close()


engine = Engine()
"""Application database engine."""
