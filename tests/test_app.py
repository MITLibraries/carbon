# -*- coding: utf-8 -*-
from __future__ import absolute_import

from lxml import etree as ET
import pytest

from carbon import people
from carbon.app import PersonFeed, ns, NSMAP, add_child


pytestmark = pytest.mark.usefixtures('load_data')


def test_people_generates_people():
    peeps = people()
    person = next(peeps)
    assert person['KRB_NAME'] == 'foobar'
    person = next(peeps)
    assert person['KRB_NAME'] == 'foobaz'


def test_add_child_adds_child_element(E):
    xml = E.records(
        E.record('foobar', {'baz': 'bazbar'})
    )
    e = ET.Element(ns('records'), nsmap=NSMAP)
    add_child(e, 'record', 'foobar', baz='bazbar')
    assert ET.tostring(e) == ET.tostring(xml)


def test_person_feed_uses_namespace():
    p = PersonFeed()
    assert p._root.tag == "{http://www.symplectic.co.uk/hrimporter}records"


def test_person_feed_adds_person(E):
    xml = E.records(
        E.record(
            E.field('1234', {'name': '[Proprietary_ID]'}),
            E.field('foobar', {'name': '[Username]'})
        )
    )
    p = PersonFeed()
    p.add({'MIT_ID': '1234', 'KRB_NAME': 'foobar'})
    assert p.bytes() == ET.tostring(xml)
