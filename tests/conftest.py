import os
import socket
import tempfile
import threading
from contextlib import closing

import botocore
import pytest
import yaml
from botocore.stub import Stubber
from lxml.builder import ElementMaker
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import TLS_FTPHandler
from pyftpdlib.servers import FTPServer

from carbon.config import Config
from carbon.database import DatabaseEngine, aa_articles, dlcs, metadata, orcids, persons


# set environment variables required for testing
@pytest.fixture(autouse=True)
def _test_env(ftp_server, monkeypatch):
    ftp_socket, _ = ftp_server
    monkeypatch.setenv("FEED_TYPE", "test_feed_type")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("SENTRY_DSN", "None")
    monkeypatch.setenv(
        "SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:test_sns_topic"
    )
    monkeypatch.setenv("WORKSPACE", "test")
    monkeypatch.setenv(
        "DATAWAREHOUSE_CLOUDCONNECTOR_JSON", '{"CONNECTION_STRING": "sqlite://"}'
    )
    monkeypatch.setenv("SYMPLECTIC_FTP_PATH", "/people.xml")
    monkeypatch.setenv(
        "SYMPLECTIC_FTP_JSON",
        (
            '{"SYMPLECTIC_FTP_HOST": "localhost", '
            f'"SYMPLECTIC_FTP_PORT": "{ftp_socket[1]}",'
            '"SYMPLECTIC_FTP_USER": "user", '
            '"SYMPLECTIC_FTP_PASS": "pass"}'
        ),
    )


@pytest.fixture(autouse=True)
def config(_test_env):
    return Config()


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
def articles_element_maker():
    return ElementMaker()


@pytest.fixture
def articles_element(articles_element_maker):
    articles_elements = [
        articles_element_maker.ARTICLE(
            articles_element_maker.AA_MATCH_SCORE("0.9"),
            articles_element_maker.ARTICLE_ID("1234567"),
            articles_element_maker.ARTICLE_TITLE(
                "Interaction between hatsopoulos microfluids and "
                "the Yawning Abyss of Chaos ☈."
            ),
            articles_element_maker.ARTICLE_YEAR("1999"),
            articles_element_maker.AUTHORS("McRandallson, Randall M.|Lord, Dark|☭"),
            articles_element_maker.DOI("10.0000/1234LETTERS56"),
            articles_element_maker.ISSN_ELECTRONIC("0987654"),
            articles_element_maker.ISSN_PRINT("01234567"),
            articles_element_maker.IS_CONFERENCE_PROCEEDING("0"),
            articles_element_maker.JOURNAL_FIRST_PAGE("666"),
            articles_element_maker.JOURNAL_LAST_PAGE("666"),
            articles_element_maker.JOURNAL_ISSUE("10"),
            articles_element_maker.JOURNAL_VOLUME("1"),
            articles_element_maker.JOURNAL_NAME("Bunnies"),
            articles_element_maker.MIT_ID("123456789"),
            articles_element_maker.PUBLISHER("MIT Press"),
        )
    ]
    return articles_element_maker.ARTICLES(*articles_elements)


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
def setup_stubbed_sns_client(actions):
    feed = os.environ.get("FEED_TYPE", "")
    stage = os.environ.get("SYMPLECTIC_FTP_PATH", "").lstrip("/").split("/")[0]
    request_response_payloads = {
        "start": (
            {
                "TopicArn": "arn:aws:sns:us-east-1:123456789012:test_sns_topic",
                "Subject": "Carbon run",
                "Message": (
                    f"[2023-08-18T00:00:00+00:00] Starting carbon run for the "
                    f"{feed} feed in the {stage} environment."
                ),
            },
            {"MessageId": "StartMessageId"},
        ),
        "success": (
            {
                "TopicArn": "arn:aws:sns:us-east-1:123456789012:test_sns_topic",
                "Subject": "Carbon run",
                "Message": (
                    f"[2023-08-18T00:00:00+00:00] Finished carbon run for the "
                    f"{feed} feed in the {stage} environment."
                ),
            },
            {"MessageId": "SuccessMessageId"},
        ),
        "fail": (
            {
                "TopicArn": "arn:aws:sns:us-east-1:123456789012:test_sns_topic",
                "Subject": "Carbon run",
                "Message": (
                    f"[2023-08-18T00:00:00+00:00] The following problem was "
                    f"encountered during the carbon run for the {feed} feed "
                    f"in the {stage} environment: {None}."
                ),
            },
            {"MessageId": "FailMessageId"},
        ),
    }
    sns_client = botocore.session.get_session().create_client(
        "sns", region_name="us-east-1"
    )
    stubber = Stubber(sns_client)
    for action in actions:
        request, response = request_response_payloads[action]
        stubber.add_response(
            "publish",
            response,
            request,
        )
    stubber.activate()
    return sns_client, stubber


@pytest.fixture
def stubbed_sns_client_start():
    sns_client, stubber = setup_stubbed_sns_client(["start"])
    with stubber:
        yield sns_client


@pytest.fixture
def stubbed_sns_client_success():
    sns_client, stubber = setup_stubbed_sns_client(["success"])
    with stubber:
        yield sns_client


@pytest.fixture
def stubbed_sns_client_fail():
    sns_client, stubber = setup_stubbed_sns_client(["fail"])
    with stubber:
        yield sns_client


@pytest.fixture
def stubbed_sns_client_start_success():
    sns_client, stubber = setup_stubbed_sns_client(["start", "success"])
    with stubber:
        yield sns_client


@pytest.fixture
def stubbed_sns_client_start_fail():
    sns_client, stubber = setup_stubbed_sns_client(["start", "fail"])
    with stubber:
        yield sns_client
