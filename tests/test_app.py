import os
from io import BytesIO
from unittest.mock import patch

import pytest
from freezegun import freeze_time
from lxml import etree as ET

from carbon.app import (
    NSMAP,
    FTPReader,
    PipeWriter,
    Writer,
    add_child,
    article_feed,
    articles,
    group_name,
    initials,
    ns,
    people,
    person_feed,
    sns_log,
)
from carbon.config import load_config_values

pytestmark = pytest.mark.usefixtures("_load_data")


def test_people_generates_people():
    peeps = list(people())
    person = peeps[0]
    assert person["KRB_NAME_UPPERCASE"] == "FOOBAR"
    person = peeps[1]
    assert person["KRB_NAME_UPPERCASE"] == "THOR"


def test_people_adds_orcids():
    peeps = list(people())
    assert peeps[0]["ORCID"] == "http://example.com/1"


def test_people_excludes_no_emails():
    peeps = list(people())
    no_email = [x for x in peeps if x["EMAIL_ADDRESS"] is not None]
    assert len(no_email) == len(peeps)


def test_people_excludes_no_lastname():
    peeps = list(people())
    no_email = [x for x in peeps if x["LAST_NAME"] is not None]
    assert len(no_email) == len(peeps)


def test_people_excludes_no_kerberos():
    peeps = list(people())
    no_email = [x for x in peeps if x["KRB_NAME_UPPERCASE"] is not None]
    assert len(no_email) == len(peeps)


def test_people_excludes_no_mitid():
    peeps = list(people())
    no_email = [x for x in peeps if x["MIT_ID"] is not None]
    assert len(no_email) == len(peeps)


def test_initials_returns_first_and_middle():
    assert initials("Foo", "Bar") == "F B"
    assert initials("Foo") == "F"
    assert initials("F", "B") == "F B"
    assert initials("Foo-bar", "Gaz") == "F-B G"
    assert initials("Foo Bar-baz", "G") == "F B-B G"
    assert initials("Foo", "") == "F"
    assert initials("Foo", None) == "F"
    assert initials("Gull-Þóris") == "G-Þ"
    assert initials("владимир", "ильич", "ленин") == "В И Л"  # noqa: RUF001
    assert initials("F. M.", "Laxdæla") == "F M L"


def test_add_child_adds_child_element(e):
    xml = e.records(e.record("foobar", {"baz": "bazbar"}))
    element = ET.Element(ns("records"), nsmap=NSMAP)
    add_child(element, "record", "foobar", baz="bazbar")
    assert ET.tostring(element) == ET.tostring(xml)


def test_writer_writes_person_feed():
    b = BytesIO()
    w = Writer(b)
    w.write("people")
    xml = ET.XML(b.getvalue())
    xp = xml.xpath(
        "/s:records/s:record/s:field[@name='[FirstName]']",
        namespaces={"s": "http://www.symplectic.co.uk/hrimporter"},
    )
    assert xp[1].text == "Þorgerðr"


def test_pipewriter_writes_person_feed(reader):
    r, w = os.pipe()
    with open(r, "rb") as fr, open(w, "wb") as fw:
        wtr = PipeWriter(fw)
        rdr = reader(fr)
        wtr.pipe(rdr).write("people")
    xml = ET.XML(rdr.data)
    xp = xml.xpath(
        "/s:records/s:record/s:field[@name='[FirstName]']",
        namespaces={"s": "http://www.symplectic.co.uk/hrimporter"},
    )
    assert xp[1].text == "Þorgerðr"


def test_ftpreader_sends_file(ftp_server_wrapper):
    s, d = ftp_server_wrapper
    b = BytesIO(b"Storin' some bits in the FTPz")
    ftp = FTPReader(b, "user", "pass", "/warez", port=s[1])
    ftp()
    with open(os.path.join(d, "warez")) as fp:
        assert fp.read() == "Storin' some bits in the FTPz"


def test_person_feed_uses_namespace():
    b = BytesIO()
    with person_feed(b):
        pass
    root = ET.XML(b.getvalue())
    assert root.tag == "{http://www.symplectic.co.uk/hrimporter}records"


def test_person_feed_adds_person(records, xml_records, e):
    b = BytesIO()
    xml = e.records(xml_records[0])
    r = records[0]["person"].copy()
    r.update(records[0]["orcid"])
    r.update(records[0]["dlc"])
    with person_feed(b) as f:
        f(r)
    xml = ET.XML(b.getvalue())
    xp = xml.xpath(
        "/s:records/s:record/s:field[@name='[FirstName]']",
        namespaces={"s": "http://www.symplectic.co.uk/hrimporter"},
    )
    assert xp[0].text == "Foobar"


def test_person_feed_uses_utf8_encoding(records, xml_records, e):
    b = BytesIO()
    xml = e.records(xml_records[1])
    r = records[1]["person"].copy()
    r.update(records[1]["orcid"])
    r.update(records[1]["dlc"])
    with person_feed(b) as f:
        f(r)
    xml = ET.XML(b.getvalue())
    xp = xml.xpath(
        "/s:records/s:record/s:field[@name='[FirstName]']",
        namespaces={"s": "http://www.symplectic.co.uk/hrimporter"},
    )
    assert xp[0].text == "Þorgerðr"


def test_group_name_adds_faculty():
    assert group_name("FOOBAR", "CFAT") == "FOOBAR Faculty"
    assert group_name("FOOBAR", "CFAN") == "FOOBAR Faculty"


def test_group_name_adds_non_faculty():
    assert group_name("FOOBAR", "COAC") == "FOOBAR Non-faculty"


def test_articles_generates_articles():
    arts = list(articles())
    assert "Yawning Abyss of Chaos" in arts[0]["ARTICLE_TITLE"]


def test_article_feed_adds_article(aa_data, articles_data):
    b = BytesIO()
    with article_feed(b) as f:
        f(aa_data[0])
    assert b.getvalue() == ET.tostring(
        articles_data, encoding="UTF-8", xml_declaration=True
    )


def test_articles_skips_articles_without_required_fields():
    arts = list(articles())
    assert len(arts) == 1


@freeze_time("2023-08-18")
def test_sns_log(caplog, stubbed_sns_client):
    config_values = load_config_values()
    with patch("boto3.client") as mocked_boto_client:
        mocked_boto_client.return_value = stubbed_sns_client
        sns_log(config_values, status="start")

        sns_log(config_values, status="success")
        assert "Carbon run has successfully completed." in caplog.text

        sns_log(config_values, status="fail")
        assert "Carbon run has failed." in caplog.text
