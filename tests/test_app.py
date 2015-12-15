# -*- coding: utf-8 -*-
from __future__ import absolute_import
from io import BytesIO

from lxml import etree as ET
import pytest

from carbon import people
from carbon.app import person_feed, ns, NSMAP, add_child, initials


pytestmark = pytest.mark.usefixtures('load_data')


def test_people_generates_people():
    peeps = list(people())
    person = peeps[0]
    assert person['KRB_NAME'] == 'foobar'
    person = peeps[1]
    assert person['KRB_NAME'] == 'thor'


def test_initials_returns_first_and_middle():
    assert initials('Foo', 'Bar') == 'F B'
    assert initials('Foo') == 'F'
    assert initials('F', 'B') == 'F B'
    assert initials('Foo-bar', 'Gaz') == 'F-B G'
    assert initials('Foo Bar-baz', 'G') == 'F B-B G'
    assert initials('Foo', '') == 'F'
    assert initials('Foo', None) == 'F'
    assert initials(u'Gull-Þóris') == u'G-Þ'
    assert initials(u'владимир', u'ильич', u'ленин') == u'В И Л'
    assert initials('F. M.', u'Laxdæla') == 'F M L'


def test_add_child_adds_child_element(E):
    xml = E.records(
        E.record('foobar', {'baz': 'bazbar'})
    )
    e = ET.Element(ns('records'), nsmap=NSMAP)
    add_child(e, 'record', 'foobar', baz='bazbar')
    assert ET.tostring(e) == ET.tostring(xml)


def test_person_feed_uses_namespace():
    b = BytesIO()
    with person_feed(b):
        pass
    root = ET.fromstring(b.getvalue())
    assert root.tag == "{http://www.symplectic.co.uk/hrimporter}records"


def test_person_feed_adds_person(records, xml_records, E):
    b = BytesIO()
    xml = E.records(xml_records[0])
    with person_feed(b) as f:
        f(records[0])
    assert b.getvalue() == ET.tostring(xml, encoding="UTF-8",
                                       xml_declaration=True)


def test_person_feed_uses_utf8_encoding(records, xml_records, E):
    b = BytesIO()
    xml = E.records(xml_records[1])
    with person_feed(b) as f:
        f(records[1])
    assert b.getvalue() == ET.tostring(xml, encoding="UTF-8",
                                       xml_declaration=True)