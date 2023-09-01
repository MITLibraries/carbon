import os
from io import BytesIO
from unittest.mock import patch

import pytest
from freezegun import freeze_time
from lxml import etree as ET

from carbon.app import (
    FtpFileWriter,
    PipeWriter,
    Writer,
    add_child,
    article_feed,
    articles,
    get_group_name,
    get_initials,
    people,
    person_feed,
)
from carbon.config import load_config_values
from carbon.helpers import sns_log

pytestmark = pytest.mark.usefixtures("_load_data")
symplectic_elements_namespace = "http://www.symplectic.co.uk/hrimporter"
qualified_tag_name = ET.QName(symplectic_elements_namespace, tag="records")
nsmap = {None: symplectic_elements_namespace}


def test_people_generates_people(functional_engine):
    people_records = list(people(engine=functional_engine))
    person = people_records[0]
    assert person["KRB_NAME_UPPERCASE"] == "FOOBAR"
    person = people_records[1]
    assert person["KRB_NAME_UPPERCASE"] == "THOR"


def test_people_adds_orcids(functional_engine):
    people_records = list(people(engine=functional_engine))
    assert people_records[0]["ORCID"] == "http://example.com/1"


def test_people_excludes_records_without_email(functional_engine):
    people_records = list(people(engine=functional_engine))
    people_without_emails = [
        person for person in people_records if person["EMAIL_ADDRESS"] is None
    ]
    assert len(people_without_emails) == 0


def test_people_excludes_records_without_last_name(functional_engine):
    people_records = list(people(engine=functional_engine))
    people_without_last_names = [
        person for person in people_records if person["LAST_NAME"] is None
    ]
    assert len(people_without_last_names) == 0


def test_people_excludes_records_without_kerberos(functional_engine):
    people_records = list(people(engine=functional_engine))
    people_without_kerberos = [
        person for person in people_records if person["KRB_NAME_UPPERCASE"] is None
    ]
    assert len(people_without_kerberos) == 0


def test_people_excludes_records_without_mit_id(functional_engine):
    people_records = list(people(engine=functional_engine))
    people_without_mit_id = [
        person for person in people_records if person["MIT_ID"] is None
    ]
    assert len(people_without_mit_id) == 0


def test_initials_returns_first_and_middle():
    assert get_initials("Foo", "Bar") == "F B"
    assert get_initials("Foo") == "F"
    assert get_initials("F", "B") == "F B"
    assert get_initials("Foo-bar", "Gaz") == "F-B G"
    assert get_initials("Foo Bar-baz", "G") == "F B-B G"
    assert get_initials("Foo", "") == "F"
    assert get_initials("Foo", None) == "F"
    assert get_initials("Gull-Þóris") == "G-Þ"
    assert get_initials("владимир", "ильич", "ленин") == "В И Л"  # noqa: RUF001
    assert get_initials("F. M.", "Laxdæla") == "F M L"


def test_add_child_adds_child_element(people_element_maker):
    xml = people_element_maker.records(
        people_element_maker.record("foobar", {"baz": "bazbar"})
    )
    element = ET.Element(_tag=qualified_tag_name, nsmap=nsmap)
    add_child(element, "record", "foobar", baz="bazbar")
    assert ET.tostring(element) == ET.tostring(xml)


def test_writer_writes_person_feed(functional_engine):
    output_file = BytesIO()
    writer = Writer(functional_engine, output_file)
    writer.write("people")
    xml = ET.XML(output_file.getvalue())
    xp = xml.xpath(
        "/s:records/s:record/s:field[@name='[FirstName]']",
        namespaces={"s": "http://www.symplectic.co.uk/hrimporter"},
    )
    assert xp[1].text == "Þorgerðr"


def test_pipewriter_writes_person_feed(reader, functional_engine):
    read_file, write_file = os.pipe()
    with open(read_file, "rb") as buffered_reader, open(
        write_file, "wb"
    ) as buffered_writer:
        file = reader(buffered_reader)
        writer = PipeWriter(
            engine=functional_engine, input_file=buffered_writer, ftp_output_file=file
        )
        writer.write("people")
    people_element = ET.XML(file.data)
    people_first_names_xpath = people_element.xpath(
        "/s:records/s:record/s:field[@name='[FirstName]']",
        namespaces={"s": "http://www.symplectic.co.uk/hrimporter"},
    )
    assert people_first_names_xpath[1].text == "Þorgerðr"


def test_ftp_file_writer_sends_file(ftp_server_wrapper):
    ftp_socket, ftp_directory = ftp_server_wrapper
    feed = BytesIO(b"File uploaded to FTP server.")
    ftp = FtpFileWriter(
        content_feed=feed,
        user="user",
        password="pass",  # noqa: S106
        path="/DEV",
        port=ftp_socket[1],
    )
    ftp()
    with open(os.path.join(ftp_directory, "DEV")) as file:
        assert file.read() == "File uploaded to FTP server."


def test_person_feed_uses_namespace():
    output_file = BytesIO()
    with person_feed(output_file):
        pass
    root = ET.XML(output_file.getvalue())
    assert root.tag == "{http://www.symplectic.co.uk/hrimporter}records"


def test_person_feed_adds_person(people_records):
    output_file = BytesIO()
    record = people_records[0]["person"].copy()
    record |= people_records[0]["orcid"] | people_records[0]["dlc"]
    with person_feed(output_file) as write_to_file:
        write_to_file(record)
    person_element = ET.XML(output_file.getvalue())
    person_first_name_xpath = person_element.xpath(
        "/s:records/s:record/s:field[@name='[FirstName]']",
        namespaces={"s": "http://www.symplectic.co.uk/hrimporter"},
    )
    assert person_first_name_xpath[0].text == "Foobar"


def test_person_feed_uses_utf8_encoding(people_records):
    output_file = BytesIO()
    record = people_records[1]["person"].copy()
    record |= people_records[1]["orcid"] | people_records[1]["dlc"]
    with person_feed(output_file) as write_to_file:
        write_to_file(record)
    person_element = ET.XML(output_file.getvalue())
    person_first_name_xpath = person_element.xpath(
        "/s:records/s:record/s:field[@name='[FirstName]']",
        namespaces={"s": "http://www.symplectic.co.uk/hrimporter"},
    )
    assert person_first_name_xpath[0].text == "Þorgerðr"


def test_group_name_adds_faculty():
    assert get_group_name("FOOBAR", "CFAT") == "FOOBAR Faculty"
    assert get_group_name("FOOBAR", "CFAN") == "FOOBAR Faculty"


def test_group_name_adds_non_faculty():
    assert get_group_name("FOOBAR", "COAC") == "FOOBAR Non-faculty"


def test_articles_generates_articles(functional_engine):
    articles_records = list(articles(engine=functional_engine))
    assert "Yawning Abyss of Chaos" in articles_records[0]["ARTICLE_TITLE"]


def test_article_feed_adds_article(articles_records, articles_element):
    output_file = BytesIO()
    with article_feed(output_file) as write_to_file:
        write_to_file(articles_records[0])
    assert output_file.getvalue() == ET.tostring(
        articles_element, encoding="UTF-8", xml_declaration=True
    )


def test_articles_skips_articles_without_required_fields(functional_engine):
    articles_records = list(articles(engine=functional_engine))
    assert len(articles_records) == 1


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
