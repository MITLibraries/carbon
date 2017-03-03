# -*- coding: utf-8 -*-
from __future__ import absolute_import
from io import BytesIO

from lxml import etree as ET
import pytest

from carbon import people, articles
from carbon.app import (person_feed, ns, NSMAP, add_child, initials,
                        article_feed, group_name)


pytestmark = pytest.mark.usefixtures('load_data')


def test_people_generates_people():
    peeps = list(people())
    person = peeps[0]
    assert person['KRB_NAME_UPPERCASE'] == 'FOOBAR'
    person = peeps[1]
    assert person['KRB_NAME_UPPERCASE'] == 'THOR'


def test_people_adds_orcids():
    peeps = list(people())
    assert peeps[0]['ORCID'] == 'http://example.com/1'


def test_people_excludes_no_emails():
    peeps = list(people())
    no_email = [x for x in peeps if x['EMAIL_ADDRESS'] is not None]
    assert len(no_email) == len(peeps)


def test_people_excludes_no_lastname():
    peeps = list(people())
    no_email = [x for x in peeps if x['LAST_NAME'] is not None]
    assert len(no_email) == len(peeps)


def test_people_excludes_no_kerberos():
    peeps = list(people())
    no_email = [x for x in peeps if x['KRB_NAME_UPPERCASE'] is not None]
    assert len(no_email) == len(peeps)


def test_people_excludes_no_mitid():
    peeps = list(people())
    no_email = [x for x in peeps if x['MIT_ID'] is not None]
    assert len(no_email) == len(peeps)


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
    r = records[0]['person'].copy()
    r.update(records[0]['orcid'])
    r.update(records[0]['dlc'])
    with person_feed(b) as f:
        f(r)
    assert b.getvalue() == ET.tostring(xml, encoding="UTF-8",
                                       xml_declaration=True)


def test_person_feed_uses_utf8_encoding(records, xml_records, E):
    b = BytesIO()
    xml = E.records(xml_records[1])
    r = records[1]['person'].copy()
    r.update(records[1]['orcid'])
    r.update(records[1]['dlc'])
    with person_feed(b) as f:
        f(r)
    assert b.getvalue() == ET.tostring(xml, encoding="UTF-8",
                                       xml_declaration=True)


def test_group_name_adds_faculty():
    assert group_name('FOOBAR', 'CFAT') == 'FOOBAR Faculty'
    assert group_name('FOOBAR', 'CFAN') == 'FOOBAR Faculty'


def test_group_name_adds_non_faculty():
    assert group_name('FOOBAR', 'COAC') == 'FOOBAR Non-faculty'


def test_articles_generates_articles():
    arts = list(articles())
    assert 'Yawning Abyss of Chaos' in arts[0]['ARTICLE_TITLE']


def test_article_feed_adds_article(aa_data, articles_data):
    b = BytesIO()
    with article_feed(b) as f:
        f(aa_data[0])
    assert b.getvalue() == ET.tostring(articles_data, encoding='UTF-8',
                                       xml_declaration=True)


def test_articles_skips_articles_without_required_fields():
    arts = list(articles())
    assert len(arts) == 1
