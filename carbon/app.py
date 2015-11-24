# -*- coding: utf-8 -*-
from __future__ import absolute_import
from functools import partial

from lxml import etree as ET
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


def _ns(namespace, element):
    return ET.QName(namespace, element)


SYMPLECTIC_NS = 'http://www.symplectic.co.uk/hrimporter'
NSMAP = {None: SYMPLECTIC_NS}
ns = partial(_ns, SYMPLECTIC_NS)


def add_child(parent, element, text, **kwargs):
    """Add a subelement with text."""
    child = ET.SubElement(parent, ns(element), nsmap=NSMAP, attrib=kwargs)
    child.text = text
    return child


class PersonFeed(object):
    def __init__(self):
        self._root = ET.Element(ns('records'), nsmap=NSMAP)

    def add(self, person):
        record = ET.SubElement(self._root, ns('record'), nsmap=NSMAP)
        add_child(record, 'field', person['MIT_ID'], name='[Proprietary_ID]')
        add_child(record, 'field', person['KRB_NAME'], name='[Username]')

    def bytes(self):
        return ET.tostring(self._root, encoding="UTF-8")
