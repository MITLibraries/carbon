# -*- coding: utf-8 -*-
from __future__ import absolute_import

from sqlalchemy.sql import select

from carbon.db import persons, session


def people():
    """A person generator.

    Returns an iterator of person dictionaries.
    """
    sql = select([persons])
    with session() as conn:
        for row in conn.execute(sql):
            yield dict(zip(row.keys(), row))
