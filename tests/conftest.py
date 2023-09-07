import os
import socket
import tempfile
import threading
from contextlib import closing

import botocore
import pytest
import yaml
from botocore.stub import ANY, Stubber
from lxml.builder import ElementMaker
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import TLS_FTPHandler
from pyftpdlib.servers import FTPServer

from carbon.database import DatabaseEngine, aa_articles, dlcs, metadata, orcids, persons


# set environment variables required for testing
@pytest.fixture(autouse=True)
def _test_env(ftp_server):
    ftp_socket, _ = ftp_server
    os.environ["FEED_TYPE"] = "test_feed_type"
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["SENTRY_DSN"] = "None"
    os.environ["SNS_TOPIC"] = "arn:aws:sns:us-east-1:123456789012:test_sns_topic"
    os.environ["WORKSPACE"] = "test"
    os.environ["DATAWAREHOUSE_CLOUDCONNECTOR_JSON"] = '{"CONNECTION_STRING": "sqlite://"}'
    os.environ["SYMPLECTIC_FTP_PATH"] = "/people.xml"
    os.environ["SYMPLECTIC_FTP_JSON"] = (
        '{"SYMPLECTIC_FTP_HOST": "localhost", '
        f'"SYMPLECTIC_FTP_PORT": "{ftp_socket[1]}",'
        '"SYMPLECTIC_FTP_USER": "user", '
        '"SYMPLECTIC_FTP_PASS": "pass"}'
    )


# populate sqlite test database with records
@pytest.fixture
def _load_data(functional_engine, people_records, articles_records):
    with closing(functional_engine().connect()) as connection:
        connection.execute(persons.delete())
        connection.execute(orcids.delete())
        connection.execute(dlcs.delete())
        connection.execute(aa_articles.delete())
        for record in people_records:
            connection.execute(persons.insert(), record["person"])
            connection.execute(orcids.insert(), record["orcid"])
            connection.execute(dlcs.insert(), record["dlc"])
        connection.execute(aa_articles.insert(), articles_records)
        connection.commit()
    yield
    with closing(functional_engine().connect()) as connection:
        connection.execute(persons.delete())
        connection.execute(orcids.delete())
        connection.execute(dlcs.delete())
        connection.execute(aa_articles.delete())


@pytest.fixture(scope="session")
def articles_records():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    data = os.path.join(current_dir, "fixtures/articles.yml")
    with open(data) as fp:
        return list(yaml.safe_load_all(fp))


@pytest.fixture(scope="session")
def people_records():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    data = os.path.join(current_dir, "fixtures/data.yml")
    with open(data) as fp:
        return list(yaml.safe_load_all(fp))


# create engine for tests requiring successful connections to the sqlite test database
@pytest.fixture(scope="session", autouse=True)
def functional_engine():
    engine = DatabaseEngine()
    engine.configure("sqlite://")
    metadata.create_all(bind=engine())
    return engine


# create engine for tests requiring failed connections to the sqlite test database
@pytest.fixture(scope="session")
def nonfunctional_engine():
    engine = DatabaseEngine()
    engine.configure(connection_string="sqlite:///nonexistent_directory/bad.db")
    return engine


# create XML elements representing 'people' and 'articles' records
@pytest.fixture
def articles_element():
    element_maker = ElementMaker()
    return element_maker.ARTICLES(
        element_maker.ARTICLE(
            element_maker.AA_MATCH_SCORE("0.9"),
            element_maker.ARTICLE_ID("1234567"),
            element_maker.ARTICLE_TITLE(
                "Interaction between hatsopoulos microfluids and "
                "the Yawning Abyss of Chaos ☈."
            ),
            element_maker.ARTICLE_YEAR("1999"),
            element_maker.AUTHORS("McRandallson, Randall M.|Lord, Dark|☭"),
            element_maker.DOI("10.0000/1234LETTERS56"),
            element_maker.ISSN_ELECTRONIC("0987654"),
            element_maker.ISSN_PRINT("01234567"),
            element_maker.IS_CONFERENCE_PROCEEDING("0"),
            element_maker.JOURNAL_FIRST_PAGE("666"),
            element_maker.JOURNAL_LAST_PAGE("666"),
            element_maker.JOURNAL_ISSUE("10"),
            element_maker.JOURNAL_VOLUME("1"),
            element_maker.JOURNAL_NAME("Bunnies"),
            element_maker.MIT_ID("123456789"),
            element_maker.PUBLISHER("MIT Press"),
        )
    )


@pytest.fixture
def people_element_maker():
    return ElementMaker(
        namespace="http://www.symplectic.co.uk/hrimporter",
        nsmap={None: "http://www.symplectic.co.uk/hrimporter"},
    )


@pytest.fixture
def people_element(people_element_maker):
    people_elements = [
        people_element_maker.record(
            people_element_maker.field("123456", {"name": "[Proprietary_ID]"}),
            people_element_maker.field("FOOBAR", {"name": "[Username]"}),
            people_element_maker.field("F B", {"name": "[Initials]"}),
            people_element_maker.field("Gaz", {"name": "[LastName]"}),
            people_element_maker.field("Foobar", {"name": "[FirstName]"}),
            people_element_maker.field("foobar@example.com", {"name": "[Email]"}),
            people_element_maker.field("MIT", {"name": "[AuthenticatingAuthority]"}),
            people_element_maker.field("1", {"name": "[IsAcademic]"}),
            people_element_maker.field("1", {"name": "[IsCurrent]"}),
            people_element_maker.field("1", {"name": "[LoginAllowed]"}),
            people_element_maker.field(
                "Chemistry Faculty", {"name": "[PrimaryGroupDescriptor]"}
            ),
            people_element_maker.field("2001-01-01", {"name": "[ArriveDate]"}),
            people_element_maker.field("2010-01-01", {"name": "[LeaveDate]"}),
            people_element_maker.field("http://example.com/1", {"name": "[Generic01]"}),
            people_element_maker.field("CFAT", {"name": "[Generic02]"}),
            people_element_maker.field("SCIENCE AREA", {"name": "[Generic03]"}),
            people_element_maker.field("Chemistry", {"name": "[Generic04]"}),
            people_element_maker.field(name="[Generic05]"),
        ),
        people_element_maker.record(
            people_element_maker.field("098754", name="[Proprietary_ID]"),
            people_element_maker.field("THOR", name="[Username]"),
            people_element_maker.field("Þ H", name="[Initials]"),
            people_element_maker.field("Hammerson", name="[LastName]"),
            people_element_maker.field("Þorgerðr", name="[FirstName]"),
            people_element_maker.field("thor@example.com", name="[Email]"),
            people_element_maker.field("MIT", {"name": "[AuthenticatingAuthority]"}),
            people_element_maker.field("1", {"name": "[IsAcademic]"}),
            people_element_maker.field("1", {"name": "[IsCurrent]"}),
            people_element_maker.field("1", {"name": "[LoginAllowed]"}),
            people_element_maker.field(
                "Nuclear Science Non-faculty",
                {"name": "[PrimaryGroupDescriptor]"},
            ),
            people_element_maker.field("2015-01-01", {"name": "[ArriveDate]"}),
            people_element_maker.field("2999-12-31", {"name": "[LeaveDate]"}),
            people_element_maker.field("http://example.com/2", {"name": "[Generic01]"}),
            people_element_maker.field("COAC", {"name": "[Generic02]"}),
            people_element_maker.field("ENGINEERING AREA", {"name": "[Generic03]"}),
            people_element_maker.field("Nuclear Science", {"name": "[Generic04]"}),
            people_element_maker.field(
                "Nuclear Science and Engineering", {"name": "[Generic05]"}
            ),
        ),
    ]

    return people_element_maker.records(*people_elements)


# fixtures for mocking an FTP server and a buffered reader
@pytest.fixture(scope="session")
def ftp_server():
    """Starts an FTPS server with an empty temp dir.

    This fixture returns a tuple with the socketname and the path to the
    serving directory. The socketname is a tuple with host and port.

    Use the ``ftp_server`` wrapper fixture instead as it will clean the
    directory before each test.
    """
    ftp_socket = socket.socket()
    ftp_socket.bind(("", 0))
    fixtures = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")
    with tempfile.TemporaryDirectory() as ftp_directory:
        auth = DummyAuthorizer()
        auth.add_user("user", "pass", ftp_directory, perm="elradfmwMT")
        handler = TLS_FTPHandler
        handler.certfile = os.path.join(fixtures, "server.crt")
        handler.keyfile = os.path.join(fixtures, "server.key")
        handler.authorizer = auth
        server = FTPServer(ftp_socket, handler)
        thread = threading.Thread(target=server.serve_forever, daemon=1)
        thread.start()
        yield ftp_socket.getsockname(), ftp_directory


@pytest.fixture
def ftp_server_wrapper(ftp_server):
    """Wrapper around ``_ftp_server`` to clean directory before each test."""
    ftp_directory = ftp_server[1]
    for file in os.listdir(ftp_directory):
        file_path = os.path.join(ftp_directory, file)
        if os.path.isfile(file_path):
            os.unlink(file_path)
    return ftp_server


@pytest.fixture
def reader():
    class Reader:
        def __init__(self, file):
            self.file = file
            self.data = b""

        def __call__(self):
            while 1:
                data = self.file.read(1024)
                if not data:
                    break
                self.data += data

    return Reader


# environment variables that should be updated for certain tests
@pytest.fixture
def symplectic_ftp_path(request, monkeypatch):
    monkeypatch.setenv("SYMPLECTIC_FTP_PATH", request.param)
    return request.param


@pytest.fixture
def feed_type(request, monkeypatch):
    monkeypatch.setenv("FEED_TYPE", request.param)
    return request.param


# AWS stubs for mocking cli requests
@pytest.fixture
def stubbed_sns_client():
    stage = os.environ.get("SYMPLECTIC_FTP_PATH", "").lstrip("/").split("/")[0]
    feed = os.environ.get("FEED_TYPE", "")

    sns_client = botocore.session.get_session().create_client(
        "sns", region_name="us-east-1"
    )

    expected_response = {
        "MessageId": "47e1b891-31aa-41d6-a5bf-d35b95d1027d",
        "ResponseMetadata": {
            "RequestId": "f187a3c1-376f-11df-8963-01868b7c937a",
            "HTTPStatusCode": 200,
            "RetryAttempts": 0,
        },
    }

    expected_start_params = {
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:test_sns_topic",
        "Subject": "Carbon run",
        "Message": (
            f"[2023-08-18T00:00:00+00:00] Starting carbon run for the "
            f"{feed} feed in the {stage} environment."
        ),
    }

    # ANY is used because 'Message' parameter expects a single value
    # the second call to sns_log will submit a fail or success message
    expected_fail_or_success_params = {
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:test_sns_topic",
        "Subject": "Carbon run",
        "Message": ANY,
    }

    with Stubber(sns_client) as stubber:
        # number of responses in stubber must equal number of calls to sns_log
        # responses are returned first in, first out
        stubber.add_response("publish", expected_response, expected_start_params)
        stubber.add_response(
            "publish", expected_response, expected_fail_or_success_params
        )
        stubber.add_response(
            "publish", expected_response, expected_fail_or_success_params
        )
        yield sns_client
