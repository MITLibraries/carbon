# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os

import pytest

from carbon.db import engine, session, metadata, persons


@pytest.fixture(scope="session", autouse=True)
def app_init():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    db_dir = os.path.abspath(os.path.join(current_dir, 'db'))
    if not os.path.isdir(db_dir):
        os.mkdir(db_dir)
    test_db = os.path.join(db_dir, 'test.db')
    engine.configure('sqlite:///%s' % test_db)
    metadata.bind = engine()
    metadata.create_all()


@pytest.yield_fixture
def load_data():
    with session() as s:
        s.execute(persons.delete())
    with session() as s:
        s.execute(persons.insert(), [
            {'MIT_ID': '123456', 'KRB_NAME': 'foobar'},
            {'MIT_ID': '098754', 'KRB_NAME': 'foobaz'}
        ])
    yield
    with session() as s:
        s.execute(persons.delete())
