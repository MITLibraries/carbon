import os
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from freezegun import freeze_time
from lxml import etree as ET

from carbon.cli import main
from carbon.database import engine


@pytest.fixture
def runner():
    return CliRunner()


@freeze_time("2023-08-18")
@pytest.mark.parametrize(
    ("feed_type", "symplectic_ftp_path"), [("people", "/people.xml")], indirect=True
)
@pytest.mark.usefixtures("_load_data")
def test_people_returns_people(
    feed_type,
    symplectic_ftp_path,
    runner,
    people_element,
    ftp_server,
    stubbed_sns_client,
):
    _, ftp_directory = ftp_server

    with patch("boto3.client") as mocked_boto_client:
        mocked_boto_client.return_value = stubbed_sns_client
        result = runner.invoke(main)
        assert result.exit_code == 0

    people_element = ET.parse(os.path.join(ftp_directory, "people.xml"))
    people_xml_string = ET.tostring(
        people_element, encoding="UTF-8", xml_declaration=True
    )
    assert people_xml_string == ET.tostring(
        people_element, encoding="UTF-8", xml_declaration=True
    )


@freeze_time("2023-08-18")
@pytest.mark.parametrize(
    ("feed_type", "symplectic_ftp_path"), [("articles", "/articles.xml")], indirect=True
)
@pytest.mark.usefixtures("_load_data")
def test_articles_returns_articles(
    feed_type,
    symplectic_ftp_path,
    runner,
    articles_element,
    ftp_server,
    stubbed_sns_client,
):
    _, ftp_directory = ftp_server

    with patch("boto3.client") as mocked_boto_client:
        mocked_boto_client.return_value = stubbed_sns_client
        result = runner.invoke(main)
        assert result.exit_code == 0

    articles_element = ET.parse(os.path.join(ftp_directory, "articles.xml"))
    articles_xml_string = ET.tostring(
        articles_element, encoding="UTF-8", xml_declaration=True
    )
    assert articles_xml_string == ET.tostring(
        articles_element, encoding="UTF-8", xml_declaration=True
    )


@freeze_time("2023-08-18")
@pytest.mark.parametrize(
    ("feed_type", "symplectic_ftp_path"), [("people", "/people.xml")], indirect=True
)
@pytest.mark.usefixtures("_load_data")
def test_file_is_ftped(
    feed_type,
    symplectic_ftp_path,
    monkeypatch,
    runner,
    ftp_server,
    stubbed_sns_client,
):
    ftp_socket, ftp_directory = ftp_server

    monkeypatch.setenv(
        "SYMPLECTIC_FTP_JSON",
        (
            '{"SYMPLECTIC_FTP_HOST": "localhost", '
            f'"SYMPLECTIC_FTP_PORT": "{ftp_socket[1]}",'
            '"SYMPLECTIC_FTP_USER": "user", '
            '"SYMPLECTIC_FTP_PASS": "pass"}'
        ),
    )

    with patch("boto3.client") as mocked_boto_client:
        mocked_boto_client.return_value = stubbed_sns_client
        result = runner.invoke(main)
        assert result.exit_code == 0

    assert os.path.exists(os.path.join(ftp_directory, "people.xml"))


def test_cli_connection_tests_success(caplog, runner):
    result = runner.invoke(main, ["--run_connection_tests"])
    assert result.exit_code == 0
    assert "Successfully connected to the Data Warehouse" in caplog.text
    assert "Successfully connected to the Symplectic Elements FTP server" in caplog.text


def test_cli_connection_tests_fail(caplog, ftp_server, monkeypatch, runner):
    ftp_socket, _ = ftp_server

    # override engine from pytest fixture
    # configure with connection string that will error out with engine.connect()
    engine._engine = None  # noqa: SLF001
    engine.configure(connection_string="sqlite:///nonexistent_directory/bad.db")

    monkeypatch.setenv(
        "SYMPLECTIC_FTP_JSON",
        (
            '{"SYMPLECTIC_FTP_HOST": "localhost", '
            f'"SYMPLECTIC_FTP_PORT": "{ftp_socket[1]}",'
            '"SYMPLECTIC_FTP_USER": "user", '
            '"SYMPLECTIC_FTP_PASS": "invalid_password"}'
        ),
    )
    result = runner.invoke(main, ["--run_connection_tests"])
    assert result.exit_code == 0
    assert "Failed to connect to the Data Warehouse" in caplog.text
    assert "Failed to connect to the Symplectic Elements FTP server" in caplog.text
