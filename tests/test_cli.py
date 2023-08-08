import os

import pytest
from click.testing import CliRunner
from lxml import etree as ET

from carbon.cli import main

pytestmark = pytest.mark.usefixtures("_load_data")


@pytest.fixture
def runner():
    return CliRunner()


def test_people_returns_people(runner, people_data, ftp_server):
    s, d = ftp_server
    os.environ["FEED_TYPE"] = "people"
    os.environ["SYMPLECTIC_FTP_PATH"] = "/people.xml"
    os.environ["SYMPLECTIC_FTP_JSON"] = (
        '{"SYMPLECTIC_FTP_HOST": "localhost", '
        f'"SYMPLECTIC_FTP_PORT": "{s[1]}",'
        '"SYMPLECTIC_FTP_USER": "user", '
        '"SYMPLECTIC_FTP_PASS": "pass"}'
    )

    result = runner.invoke(main)
    assert result.exit_code == 0

    people_element = ET.parse(os.path.join(d, "people.xml"))
    people_xml_string = ET.tostring(
        people_element, encoding="UTF-8", xml_declaration=True
    )
    assert people_xml_string == ET.tostring(
        people_data, encoding="UTF-8", xml_declaration=True
    )


def test_articles_returns_articles(runner, articles_data, ftp_server):
    s, d = ftp_server
    os.environ["FEED_TYPE"] = "articles"
    os.environ["SYMPLECTIC_FTP_PATH"] = "/articles.xml"
    os.environ["SYMPLECTIC_FTP_JSON"] = (
        '{"SYMPLECTIC_FTP_HOST": "localhost", '
        f'"SYMPLECTIC_FTP_PORT": "{s[1]}",'
        '"SYMPLECTIC_FTP_USER": "user", '
        '"SYMPLECTIC_FTP_PASS": "pass"}'
    )

    result = runner.invoke(main)
    assert result.exit_code == 0

    articles_element = ET.parse(os.path.join(d, "articles.xml"))
    articles_xml_string = ET.tostring(
        articles_element, encoding="UTF-8", xml_declaration=True
    )
    assert articles_xml_string == ET.tostring(
        articles_data, encoding="UTF-8", xml_declaration=True
    )


def test_file_is_ftped(runner, ftp_server):
    s, d = ftp_server
    os.environ["FEED_TYPE"] = "people"
    os.environ["SYMPLECTIC_FTP_PATH"] = "/peeps.xml"
    os.environ["SYMPLECTIC_FTP_JSON"] = (
        '{"SYMPLECTIC_FTP_HOST": "localhost", '
        f'"SYMPLECTIC_FTP_PORT": "{s[1]}",'
        '"SYMPLECTIC_FTP_USER": "user", '
        '"SYMPLECTIC_FTP_PASS": "pass"}'
    )

    result = runner.invoke(main)
    assert result.exit_code == 0
    assert os.path.exists(os.path.join(d, "peeps.xml"))
