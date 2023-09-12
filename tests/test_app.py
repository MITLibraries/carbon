import os
from io import BytesIO

import pytest
from lxml import etree as ET

from carbon.app import ConcurrentFtpFileWriter, FileWriter, FtpFile
from carbon.feed import ArticlesXmlFeed, PeopleXmlFeed

pytestmark = pytest.mark.usefixtures("_load_data")
symplectic_elements_namespace = "http://www.symplectic.co.uk/hrimporter"
qualified_tag_name = ET.QName(symplectic_elements_namespace, tag="records")
nsmap = {None: symplectic_elements_namespace}


def test_concurrent_ftp_file_writer_creates_people_xml_file(reader, functional_engine):
    read_file, write_file = os.pipe()
    with open(read_file, "rb") as buffered_reader, open(
        write_file, "wb"
    ) as buffered_writer:
        file = reader(buffered_reader)
        ftp_file_writer = ConcurrentFtpFileWriter(
            engine=functional_engine, input_file=buffered_writer, ftp_output_file=file
        )
        ftp_file_writer.write("people")
    people_element = ET.XML(file.data)
    people_first_names_xpath = people_element.xpath(
        "/s:records/s:record/s:field[@name='[FirstName]']",
        namespaces={"s": "http://www.symplectic.co.uk/hrimporter"},
    )
    assert people_first_names_xpath[1].text == "Þorgerðr"


def test_file_writer_creates_people_xml_file(functional_engine):
    file_writer = FileWriter(engine=functional_engine, output_file=BytesIO())
    file_writer.write("people")
    people_element = ET.XML(file_writer.output_file.getvalue())
    people_first_names_xpath = people_element.xpath(
        "/s:records/s:record/s:field[@name='[FirstName]']",
        namespaces={"s": "http://www.symplectic.co.uk/hrimporter"},
    )
    assert people_first_names_xpath[1].text == "Þorgerðr"


def test_ftp_file_uploads_file_to_server(ftp_server_wrapper):
    ftp_socket, ftp_directory = ftp_server_wrapper
    feed = BytesIO(b"File uploaded to FTP server.")
    ftp_file = FtpFile(
        content_feed=feed,
        user="user",
        password="pass",  # noqa: S106
        path="/DEV",
        port=ftp_socket[1],
    )
    ftp_file()
    with open(os.path.join(ftp_directory, "DEV")) as file:
        assert file.read() == "File uploaded to FTP server."


def test_people_xml_feed_adds_subelement(functional_engine, people_element_maker):
    people_xml_feed = PeopleXmlFeed(engine=functional_engine, output_file=BytesIO())
    xml = people_element_maker.records(
        people_element_maker.record("foobar", {"baz": "bazbar"})
    )
    element = ET.Element(_tag=qualified_tag_name, nsmap=nsmap)
    people_xml_feed._add_subelement(  # noqa: SLF001
        parent=element, element_name="record", element_text="foobar", baz="bazbar"
    )
    assert ET.tostring(element) == ET.tostring(xml)


def test_people_xml_feed_generates_people(functional_engine):
    people_xml_feed = PeopleXmlFeed(engine=functional_engine, output_file=BytesIO())
    people_records = people_xml_feed.records
    assert next(people_records)["KRB_NAME_UPPERCASE"] == "FOOBAR"
    assert next(people_records)["KRB_NAME_UPPERCASE"] == "THOR"


def test_people_xml_feed_query_adds_orcids(functional_engine):
    people_xml_feed = PeopleXmlFeed(engine=functional_engine, output_file=BytesIO())
    people_records = people_xml_feed.records
    assert next(people_records)["ORCID"] == "http://example.com/1"


def test_people_xml_feed_query_excludes_records_without_email(functional_engine):
    people_xml_feed = PeopleXmlFeed(engine=functional_engine, output_file=BytesIO())
    people_records = people_xml_feed.records
    people_without_emails = [
        person for person in people_records if person["EMAIL_ADDRESS"] is None
    ]
    assert len(people_without_emails) == 0


def test_people_xml_feed_query_excludes_records_without_last_name(functional_engine):
    people_xml_feed = PeopleXmlFeed(engine=functional_engine, output_file=BytesIO())
    people_records = people_xml_feed.records
    people_without_last_names = [
        person for person in people_records if person["LAST_NAME"] is None
    ]
    assert len(people_without_last_names) == 0


def test_people_xml_feed_query_excludes_records_without_kerberos(functional_engine):
    people_xml_feed = PeopleXmlFeed(engine=functional_engine, output_file=BytesIO())
    people_records = people_xml_feed.records
    people_without_kerberos = [
        person for person in people_records if person["KRB_NAME_UPPERCASE"] is None
    ]
    assert len(people_without_kerberos) == 0


def test_people_xml_feed_query_excludes_records_without_mit_id(functional_engine):
    people_xml_feed = PeopleXmlFeed(engine=functional_engine, output_file=BytesIO())
    people_records = people_xml_feed.records
    people_without_mit_id = [
        person for person in people_records if person["MIT_ID"] is None
    ]
    assert len(people_without_mit_id) == 0


def test_people_xml_feed_uses_namespace(functional_engine):
    people_xml_feed = PeopleXmlFeed(engine=functional_engine, output_file=BytesIO())
    people_xml_feed.run(nsmap=people_xml_feed.namespace_mapping)
    people_element = ET.XML(people_xml_feed.output_file.getvalue())
    assert people_element.tag == "{http://www.symplectic.co.uk/hrimporter}records"


def test_article_xml_feed_adds_subelement(articles_element_maker, functional_engine):
    articles_xml_feed = ArticlesXmlFeed(engine=functional_engine, output_file=BytesIO())
    xml = articles_element_maker.ARTICLES(articles_element_maker.ARTICLE("foobar"))
    element = ET.Element(_tag="ARTICLES")
    articles_xml_feed._add_subelement(  # noqa: SLF001
        parent=element, element_name="ARTICLE", element_text="foobar"
    )
    assert ET.tostring(element) == ET.tostring(xml)


def test_articles_xml_feed_generates_articles(functional_engine):
    articles_xml_feed = ArticlesXmlFeed(engine=functional_engine, output_file=BytesIO())
    articles_records = articles_xml_feed.records
    assert "Yawning Abyss of Chaos" in next(articles_records)["ARTICLE_TITLE"]


def test_articles_xml_feed_query_excludes_records_without_required_fields(
    functional_engine,
):
    articles_xml_feed = ArticlesXmlFeed(engine=functional_engine, output_file=BytesIO())
    articles_records = articles_xml_feed.records
    articles_without_required_fields = [
        article
        for article in articles_records
        if article["ARTICLE_ID"] is None
        and article["ARTICLE_TITLE"] is None
        and article["DOI"] is None
        and article["MIT_ID"] is None
    ]
    assert len(articles_without_required_fields) == 0
