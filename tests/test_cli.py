import os
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from freezegun import freeze_time
from lxml import etree as ET

from carbon.cli import DatabaseToFtpPipe, main


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
    ftp_server,
    functional_engine,
    people_element,
    runner,
    stubbed_sns_client_start_success,
):
    _, ftp_directory = ftp_server

    with patch("boto3.client") as mocked_sns_client, patch(
        "carbon.cli.DatabaseEngine"
    ) as mocked_engine:
        mocked_sns_client.return_value = stubbed_sns_client_start_success
        mocked_engine.return_value = functional_engine
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
    articles_element,
    ftp_server,
    functional_engine,
    runner,
    stubbed_sns_client_start_success,
):
    _, ftp_directory = ftp_server

    with patch("boto3.client") as mocked_sns_client, patch(
        "carbon.cli.DatabaseEngine"
    ) as mocked_engine:
        mocked_engine.return_value = functional_engine
        mocked_sns_client.return_value = stubbed_sns_client_start_success
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
    ftp_server,
    functional_engine,
    runner,
    stubbed_sns_client_start_success,
):
    _, ftp_directory = ftp_server

    with patch("boto3.client") as mocked_sns_client, patch(
        "carbon.cli.DatabaseEngine"
    ) as mocked_engine:
        mocked_engine.return_value = functional_engine
        mocked_sns_client.return_value = stubbed_sns_client_start_success
        result = runner.invoke(main)
        assert result.exit_code == 0

    assert os.path.exists(os.path.join(ftp_directory, "people.xml"))


@freeze_time("2023-08-18")
@pytest.mark.parametrize(
    ("feed_type", "symplectic_ftp_path"), [("people", "/people.xml")], indirect=True
)
@pytest.mark.usefixtures("_load_data")
def test_cli_sns_log_is_ignored_with_flag(
    feed_type,
    symplectic_ftp_path,
    caplog,
    functional_engine,
    runner,
    stubbed_sns_client_start_success,
):
    with patch("boto3.client") as mocked_sns_client, patch(
        "carbon.cli.DatabaseEngine"
    ) as mocked_engine:
        mocked_engine.return_value = functional_engine
        mocked_sns_client.return_value = stubbed_sns_client_start_success
        result = runner.invoke(main, ["--ignore_sns_logging"])
        assert result.exit_code == 0
        assert "Carbon run has successfully completed." in caplog.text
        mocked_sns_client.assert_not_called()


@freeze_time("2023-08-18")
@pytest.mark.parametrize(
    ("feed_type", "symplectic_ftp_path"), [("people", "/people.xml")], indirect=True
)
@pytest.mark.usefixtures("_load_data")
def test_cli_sns_log_publishes_status_message_success(
    feed_type,
    symplectic_ftp_path,
    caplog,
    functional_engine,
    runner,
    stubbed_sns_client_start_success,
):
    with patch("boto3.client") as mocked_sns_client, patch(
        "carbon.cli.DatabaseEngine"
    ) as mocked_engine:
        mocked_engine.return_value = functional_engine
        mocked_sns_client.return_value = stubbed_sns_client_start_success
        result = runner.invoke(main)
        assert result.exit_code == 0
        assert "Carbon run has successfully completed." in caplog.text
        mocked_sns_client.assert_called()


@freeze_time("2023-08-18")
@pytest.mark.parametrize(
    ("feed_type", "symplectic_ftp_path"), [("people", "/people.xml")], indirect=True
)
@pytest.mark.usefixtures("_load_data")
def test_cli_sns_log_publishes_status_message_fail(
    feed_type,
    symplectic_ftp_path,
    caplog,
    functional_engine,
    runner,
    stubbed_sns_client_start_fail,
):
    with patch("boto3.client") as mocked_sns_client, patch.object(
        DatabaseToFtpPipe, "run", side_effect=Exception(None)
    ), patch("carbon.cli.DatabaseEngine") as mocked_engine:
        mocked_engine.return_value = functional_engine
        mocked_sns_client.return_value = stubbed_sns_client_start_fail
        result = runner.invoke(main)
        assert result.exit_code == 0
        assert "Carbon run has failed." in caplog.text
        mocked_sns_client.assert_called()


def test_cli_connection_tests_success(caplog, functional_engine, runner):
    with patch("carbon.cli.DatabaseEngine") as mocked_engine:
        mocked_engine.return_value = functional_engine
        result = runner.invoke(main, ["--run_connection_tests"])
        assert result.exit_code == 0

    assert "Successfully connected to the Data Warehouse" in caplog.text
    assert "Successfully connected to the Symplectic Elements FTP server" in caplog.text


def test_cli_database_connection_test_fails(caplog, nonfunctional_engine, runner):
    with patch("carbon.cli.DatabaseEngine") as mocked_engine:
        mocked_engine.return_value = nonfunctional_engine
        result = runner.invoke(main, ["--run_connection_tests"])
        assert result.exit_code == 1

    assert "Failed to connect to the Data Warehouse" in caplog.text


def test_cli_ftp_connection_test_fails(
    caplog, ftp_server, functional_engine, monkeypatch, runner
):
    ftp_socket, _ = ftp_server
    monkeypatch.setenv(
        "SYMPLECTIC_FTP_JSON",
        (
            '{"SYMPLECTIC_FTP_HOST": "localhost", '
            f'"SYMPLECTIC_FTP_PORT": "{ftp_socket[1]}",'
            '"SYMPLECTIC_FTP_USER": "user", '
            '"SYMPLECTIC_FTP_PASS": "invalid_password"}'
        ),
    )

    with patch("carbon.cli.DatabaseEngine") as mocked_engine:
        mocked_engine.return_value = functional_engine
        result = runner.invoke(main, ["--run_connection_tests"])
        assert result.exit_code == 1

    assert "Failed to connect to the Symplectic Elements FTP server" in caplog.text
