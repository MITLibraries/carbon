import os
import socket
import tempfile
import threading
from contextlib import closing

import pytest
import yaml
from lxml.builder import E as B
from lxml.builder import ElementMaker
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import TLS_FTPHandler
from pyftpdlib.servers import FTPServer

from carbon.db import aa_articles, dlcs, engine, metadata, orcids, persons


@pytest.fixture(scope="session", autouse=True)
def _app_init():
    engine.configure("sqlite://")
    metadata.create_all(bind=engine())


@pytest.fixture(autouse=True)
def test_env(ftp_server):
    os.environ = {
        "FEED_TYPE": "test_feed_type",
        "LOG_LEVEL": "INFO",
        "SENTRY_DSN": "test_sentry_dsn",
        "SNS_TOPIC": "test_sns_topic",
        "SYMPLECTIC_FTP_PATH": "test_symplectic_ftp_path",
        "WORKSPACE": "test",
        "DATAWAREHOUSE_CLOUDCONNECTOR_JSON": '{"CONNECTION_STRING": "sqlite://"}',
        "SYMPLECTIC_FTP_JSON": (
            '{"SYMPLECTIC_FTP_HOST": "test_symplectic_host", '
            '"SYMPLECTIC_FTP_USER": "test_user", '
            '"SYMPLECTIC_FTP_PASS": "test_pass"}'
        ),
    }

    yield


@pytest.fixture(scope="session")
def records():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    data = os.path.join(current_dir, "fixtures/data.yml")
    with open(data) as fp:
        return list(yaml.safe_load_all(fp))


@pytest.fixture(scope="session")
def aa_data():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    data = os.path.join(current_dir, "fixtures/articles.yml")
    with open(data) as fp:
        return list(yaml.safe_load_all(fp))


@pytest.fixture(scope="session")
def ftp_server():
    """Starts an FTPS server with an empty temp dir.

    This fixture returns a tuple with the socketname and the path to the
    serving directory. The socketname is a tuple with host and port.

    Use the ``ftp_server`` wrapper fixture instead as it will clean the
    directory before each test.
    """
    s = socket.socket()
    s.bind(("", 0))
    fixtures = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")
    with tempfile.TemporaryDirectory() as d:
        auth = DummyAuthorizer()
        auth.add_user("user", "pass", d, perm="elradfmwMT")
        handler = TLS_FTPHandler
        handler.certfile = os.path.join(fixtures, "server.crt")
        handler.keyfile = os.path.join(fixtures, "server.key")
        handler.authorizer = auth
        server = FTPServer(s, handler)
        t = threading.Thread(target=server.serve_forever, daemon=1)
        t.start()
        yield s.getsockname(), d


@pytest.fixture
def ftp_server_wrapper(ftp_server):
    """Wrapper around ``_ftp_server`` to clean directory before each test."""
    d = ftp_server[1]
    for f in os.listdir(d):
        fpath = os.path.join(d, f)
        if os.path.isfile(fpath):
            os.unlink(fpath)
    return ftp_server


@pytest.fixture
def _load_data(records, aa_data):
    with closing(engine().connect()) as conn:
        conn.execute(persons.delete())
        conn.execute(orcids.delete())
        conn.execute(dlcs.delete())
        conn.execute(aa_articles.delete())
        for r in records:
            conn.execute(persons.insert(), r["person"])
            conn.execute(orcids.insert(), r["orcid"])
            conn.execute(dlcs.insert(), r["dlc"])
        conn.execute(aa_articles.insert(), aa_data)
        conn.commit()
    yield
    with closing(engine().connect()) as conn:
        conn.execute(persons.delete())
        conn.execute(orcids.delete())
        conn.execute(dlcs.delete())
        conn.execute(aa_articles.delete())


@pytest.fixture
def xml_records(e):
    return [
        e.record(
            e.field("123456", {"name": "[Proprietary_ID]"}),
            e.field("FOOBAR", {"name": "[Username]"}),
            e.field("F B", {"name": "[Initials]"}),
            e.field("Gaz", {"name": "[LastName]"}),
            e.field("Foobar", {"name": "[FirstName]"}),
            e.field("foobar@example.com", {"name": "[Email]"}),
            e.field("MIT", {"name": "[AuthenticatingAuthority]"}),
            e.field("1", {"name": "[IsAcademic]"}),
            e.field("1", {"name": "[IsCurrent]"}),
            e.field("1", {"name": "[LoginAllowed]"}),
            e.field("Chemistry Faculty", {"name": "[PrimaryGroupDescriptor]"}),
            e.field("2001-01-01", {"name": "[ArriveDate]"}),
            e.field("2010-01-01", {"name": "[LeaveDate]"}),
            e.field("http://example.com/1", {"name": "[Generic01]"}),
            e.field("CFAT", {"name": "[Generic02]"}),
            e.field("SCIENCE AREA", {"name": "[Generic03]"}),
            e.field("Chemistry", {"name": "[Generic04]"}),
            e.field(name="[Generic05]"),
        ),
        e.record(
            e.field("098754", name="[Proprietary_ID]"),
            e.field("THOR", name="[Username]"),
            e.field("Þ H", name="[Initials]"),
            e.field("Hammerson", name="[LastName]"),
            e.field("Þorgerðr", name="[FirstName]"),
            e.field("thor@example.com", name="[Email]"),
            e.field("MIT", {"name": "[AuthenticatingAuthority]"}),
            e.field("1", {"name": "[IsAcademic]"}),
            e.field("1", {"name": "[IsCurrent]"}),
            e.field("1", {"name": "[LoginAllowed]"}),
            e.field(
                "Nuclear Science Non-faculty",
                {"name": "[PrimaryGroupDescriptor]"},
            ),
            e.field("2015-01-01", {"name": "[ArriveDate]"}),
            e.field("2999-12-31", {"name": "[LeaveDate]"}),
            e.field("http://example.com/2", {"name": "[Generic01]"}),
            e.field("COAC", {"name": "[Generic02]"}),
            e.field("ENGINEERING AREA", {"name": "[Generic03]"}),
            e.field("Nuclear Science", {"name": "[Generic04]"}),
            e.field("Nuclear Science and Engineering", {"name": "[Generic05]"}),
        ),
    ]


@pytest.fixture
def xml_data(e, xml_records):
    return e.records(*xml_records)


@pytest.fixture
def e():
    return ElementMaker(
        namespace="http://www.symplectic.co.uk/hrimporter",
        nsmap={None: "http://www.symplectic.co.uk/hrimporter"},
    )


@pytest.fixture
def articles_data():
    return B.ARTICLES(
        B.ARTICLE(
            B.AA_MATCH_SCORE("0.9"),
            B.ARTICLE_ID("1234567"),
            B.ARTICLE_TITLE(
                "Interaction between hatsopoulos microfluids and "
                "the Yawning Abyss of Chaos ☈."
            ),
            B.ARTICLE_YEAR("1999"),
            B.AUTHORS("McRandallson, Randall M.|Lord, Dark|☭"),
            B.DOI("10.0000/1234LETTERS56"),
            B.ISSN_ELECTRONIC("0987654"),
            B.ISSN_PRINT("01234567"),
            B.IS_CONFERENCE_PROCEEDING("0"),
            B.JOURNAL_FIRST_PAGE("666"),
            B.JOURNAL_LAST_PAGE("666"),
            B.JOURNAL_ISSUE("10"),
            B.JOURNAL_VOLUME("1"),
            B.JOURNAL_NAME("Bunnies"),
            B.MIT_ID("123456789"),
            B.PUBLISHER("MIT Press"),
        )
    )


@pytest.fixture
def reader():
    class Reader:
        def __init__(self, fp):
            self.fp = fp
            self.data = b""

        def __call__(self):
            while 1:
                data = self.fp.read(1024)
                if not data:
                    break
                self.data += data

    return Reader
