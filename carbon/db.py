# -*- coding: utf-8 -*-
from __future__ import absolute_import
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Engine(object):
    _engine = None

    def configure(self, conn):
        self._engine = self._engine or create_engine(conn)
        Session.configure(bind=self._engine)


@contextmanager
def session():
    _session = Session()
    try:
        yield _session
        _session.commit()
    except:
        _session.rollback()
        raise
    finally:
        _session.close()


Session = sessionmaker()
engine = Engine()
