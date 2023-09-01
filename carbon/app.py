from __future__ import annotations

import logging
import os
import threading
from contextlib import closing, contextmanager
from datetime import datetime
from ftplib import FTP, FTP_TLS  # nosec
from functools import partial
from typing import IO, TYPE_CHECKING, Any

from lxml import etree as ET  # nosec
from sqlalchemy import func, select

from carbon.database import aa_articles, dlcs, engine, orcids, persons
from carbon.helpers import group_name, hire_date_string, initials

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from socket import socket

logger = logging.getLogger(__name__)

# variables used in query for retrieving 'people' records
AREAS = (
    "ARCHITECTURE & PLANNING AREA",
    "ENGINEERING AREA",
    "HUMANITIES, ARTS, & SOCIAL SCIENCES AREA",
    "SCIENCE AREA",
    "SLOAN SCHOOL OF MANAGEMENT AREA",
    "VP RESEARCH",
    "CHANCELLOR'S AREA",
    "OFFICE OF PROVOST AREA",
    "PROVOST AREA",
)
PS_CODES = (
    "CFAN",
    "CFAT",
    "CFEL",
    "CSRS",
    "CSRR",
    "COAC",
    "COAR",
    "L303",
)
TITLES = (
    "ADJUNCT ASSOCIATE PROFESSOR",
    "ADJUNCT PROFESSOR",
    "AFFILIATED ARTIST",
    "ASSISTANT PROFESSOR",
    "ASSOCIATE PROFESSOR",
    "ASSOCIATE PROFESSOR (NOTT)",
    "ASSOCIATE PROFESSOR (WOT)",
    "ASSOCIATE PROFESSOR OF THE PRACTICE",
    "INSTITUTE OFFICIAL - EMERITUS",
    "INSTITUTE PROFESSOR (WOT)",
    "INSTITUTE PROFESSOR EMERITUS",
    "INSTRUCTOR",
    "LECTURER",
    "LECTURER II",
    "POSTDOCTORAL ASSOCIATE",
    "POSTDOCTORAL FELLOW",
    "PRINCIPAL RESEARCH ASSOCIATE",
    "PRINCIPAL RESEARCH ENGINEER",
    "PRINCIPAL RESEARCH SCIENTIST",
    "PROFESSOR",
    "PROFESSOR (NOTT)",
    "PROFESSOR (WOT)",
    "PROFESSOR EMERITUS",
    "PROFESSOR OF THE PRACTICE",
    "RESEARCH ASSOCIATE",
    "RESEARCH ENGINEER",
    "RESEARCH FELLOW",
    "RESEARCH SCIENTIST",
    "RESEARCH SPECIALIST",
    "SENIOR LECTURER",
    "SENIOR POSTDOCTORAL ASSOCIATE",
    "SENIOR POSTDOCTORAL FELLOW",
    "SENIOR RESEARCH ASSOCIATE",
    "SENIOR RESEARCH ENGINEER",
    "SENIOR RESEARCH SCIENTIST",
    "SENIOR RESEARCH SCIENTIST (MAP)",
    "SPONSORED RESEARCH TECHNICAL STAFF",
    "SPONSORED RESEARCH TECHNICAL SUPERVISOR",
    "STAFF AFFILIATE",
    "TECHNICAL ASSISTANT",
    "TECHNICAL ASSOCIATE",
    "VISITING ASSISTANT PROFESSOR",
    "VISITING ASSOCIATE PROFESSOR",
    "VISITING ENGINEER",
    "VISITING LECTURER",
    "VISITING PROFESSOR",
    "VISITING RESEARCH ASSOCIATE",
    "VISITING SCHOLAR",
    "VISITING SCIENTIST",
    "VISITING SENIOR LECTURER",
    "PART-TIME FLEXIBLE/LL",
)


def _add_article(xml_file: IO, article: dict[str, Any]) -> None:
    """Create an XML element representing an article and write it to an output file.

    The function will create a single 'ARTICLE' element that contains subelements
    representing fields in a record from the 'AA_ARTICLE table'. The 'ARTICLE'
    element is written to an XML file.

    Args:
        xml_file (IO): A file-like object (stream) that writes to an XML file.
        article (dict[str, Any]): A record from the AA_ARTICLE table.
    """
    record = ET.Element("ARTICLE")
    add_child(record, "AA_MATCH_SCORE", str(article["AA_MATCH_SCORE"]))
    add_child(record, "ARTICLE_ID", article["ARTICLE_ID"])
    add_child(record, "ARTICLE_TITLE", article["ARTICLE_TITLE"])
    add_child(record, "ARTICLE_YEAR", article["ARTICLE_YEAR"])
    add_child(record, "AUTHORS", article["AUTHORS"])
    add_child(record, "DOI", article["DOI"])
    add_child(record, "ISSN_ELECTRONIC", article["ISSN_ELECTRONIC"])
    add_child(record, "ISSN_PRINT", article["ISSN_PRINT"])
    add_child(record, "IS_CONFERENCE_PROCEEDING", article["IS_CONFERENCE_PROCEEDING"])
    add_child(record, "JOURNAL_FIRST_PAGE", article["JOURNAL_FIRST_PAGE"])
    add_child(record, "JOURNAL_LAST_PAGE", article["JOURNAL_LAST_PAGE"])
    add_child(record, "JOURNAL_ISSUE", article["JOURNAL_ISSUE"])
    add_child(record, "JOURNAL_VOLUME", article["JOURNAL_VOLUME"])
    add_child(record, "JOURNAL_NAME", article["JOURNAL_NAME"])
    add_child(record, "MIT_ID", article["MIT_ID"])
    add_child(record, "PUBLISHER", article["PUBLISHER"])
    xml_file.write(record)


def _add_person(xml_file: IO, person: dict[str, Any]) -> None:
    """Create an XML element representing a person and write it to an output file.

    The function will create a single 'record' element that contains subelements
    representing fields from the 'HR_PERSON_EMPLOYEE_LIMITED', 'HR_ORG_UNIT',
    and 'ORCID_TO_MITID' tables. The 'record' element is written to
    to an XML file.

    Args:
        xml_file (IO): A file-like object (stream) that writes to an XML file.
        person (dict[str, Any]): A record from from a data model that includes fields
          from the 'HR_PERSON_EMPLOYEE_LIMITED', 'HR_ORG_UNIT', and 'ORCID_TO_MITID'
          tables.
    """
    record = ET.Element("record")
    add_child(record, "field", person["MIT_ID"], name="[Proprietary_ID]")
    add_child(record, "field", person["KRB_NAME_UPPERCASE"], name="[Username]")
    add_child(
        record,
        "field",
        initials(person["FIRST_NAME"], person["MIDDLE_NAME"]),
        name="[Initials]",
    )
    add_child(record, "field", person["LAST_NAME"], name="[LastName]")
    add_child(record, "field", person["FIRST_NAME"], name="[FirstName]")
    add_child(record, "field", person["EMAIL_ADDRESS"], name="[Email]")
    add_child(record, "field", "MIT", name="[AuthenticatingAuthority]")
    add_child(record, "field", "1", name="[IsAcademic]")
    add_child(record, "field", "1", name="[IsCurrent]")
    add_child(record, "field", "1", name="[LoginAllowed]")
    add_child(
        record,
        "field",
        group_name(person["DLC_NAME"], person["PERSONNEL_SUBAREA_CODE"]),
        name="[PrimaryGroupDescriptor]",
    )
    add_child(
        record,
        "field",
        hire_date_string(person["ORIGINAL_HIRE_DATE"], person["DATE_TO_FACULTY"]),
        name="[ArriveDate]",
    )
    add_child(
        record,
        "field",
        person["APPOINTMENT_END_DATE"].strftime("%Y-%m-%d"),
        name="[LeaveDate]",
    )
    add_child(record, "field", person["ORCID"], name="[Generic01]")
    add_child(record, "field", person["PERSONNEL_SUBAREA_CODE"], name="[Generic02]")
    add_child(record, "field", person["ORG_HIER_SCHOOL_AREA_NAME"], name="[Generic03]")
    add_child(record, "field", person["DLC_NAME"], name="[Generic04]")
    add_child(record, "field", person.get("HR_ORG_LEVEL5_NAME"), name="[Generic05]")
    xml_file.write(record)


def add_child(
    parent: ET._Element,  # noqa: SLF001
    element: str,
    text: str | None = None,
    **kwargs: str,
) -> ET._Element:  # noqa: SLF001
    """Add a subelement to an existing element.

    Args:
        parent (ET._Element): The root element.
        element: The tag name assigned to the subelement.
        text (str | None, optional): _description_. Defaults to None.
        **kwargs (str): See lxml.etree.SubElement for more details.

    Returns:
        ET._Element: The subelement.
    """
    child = ET.SubElement(parent, element, attrib=kwargs)
    child.text = text
    return child


@contextmanager
def article_feed(output_file: IO) -> Generator:
    """Generate XML feed of articles.

    Args:
        output_file (IO): A file-like object (stream) into which normalized XML strings
            strings are written.

    Yields:
        Generator: A function that adds an 'ARTICLE' element to an 'ARTICLES'
          root element.
    """
    with ET.xmlfile(output_file, encoding="UTF-8") as xf:
        xf.write_declaration()
        with xf.element("ARTICLES"):
            yield partial(_add_article, xf)


def articles() -> Generator[dict[str, Any], Any, None]:
    """Create a generator of article records.

    Yields:
        Generator[dict[str, Any], Any, None]: Results matching the query submitted to
            the Data Warehouse for retrieving 'articles' records.
    """
    sql = (
        select(aa_articles)
        .where(aa_articles.c.ARTICLE_ID.is_not(None))
        .where(aa_articles.c.ARTICLE_TITLE.is_not(None))
        .where(aa_articles.c.DOI.is_not(None))
        .where(aa_articles.c.MIT_ID.is_not(None))
    )
    with closing(engine().connect()) as connection:
        result = connection.execute(sql)
        for row in result:
            yield dict(zip(result.keys(), row, strict=True))


@contextmanager
def person_feed(output_file: IO) -> Generator:
    """Generate XML feed of people.

    This is a streaming XML generator for people. Output will be
    written to the provided output destination which can be a file
    or file-like object. The context manager returns a function
    which can be called repeatedly to add a person to the feed::

        with person_feed(sys.stdout) as f:
            f({"MIT_ID": "1234", ...})
            f({"MIT_ID": "5678", ...})

    Args:
        output_file (IO): A file-like object (stream) into which normalized XML
            strings are written.

    Yields:
        Generator: A function that adds a 'record' element to a 'records' root element.
          .
    """
    # namespace assigned to the xmlns attribute of the root 'records' element
    symplectic_elements_namespace = "http://www.symplectic.co.uk/hrimporter"
    qualified_tag_name = ET.QName(symplectic_elements_namespace, tag="records")
    nsmap = {None: symplectic_elements_namespace}

    with ET.xmlfile(output_file, encoding="UTF-8") as xml_file:
        xml_file.write_declaration()
        with xml_file.element(tag=qualified_tag_name, nsmap=nsmap):
            yield partial(_add_person, xml_file)


def people() -> Generator[dict[str, Any], Any, None]:
    """Create a generator of 'people' records.

    Yields:
        Generator[dict[str, Any], Any, None]: Results matching the query submitted to
            the Data Warehouse for retrieving 'people' records.
    """
    sql = (
        select(
            persons.c.MIT_ID,
            persons.c.KRB_NAME_UPPERCASE,
            persons.c.FIRST_NAME,
            persons.c.MIDDLE_NAME,
            persons.c.LAST_NAME,
            persons.c.EMAIL_ADDRESS,
            persons.c.DATE_TO_FACULTY,
            persons.c.ORIGINAL_HIRE_DATE,
            dlcs.c.DLC_NAME,
            persons.c.PERSONNEL_SUBAREA_CODE,
            persons.c.APPOINTMENT_END_DATE,
            orcids.c.ORCID,
            dlcs.c.ORG_HIER_SCHOOL_AREA_NAME,
            dlcs.c.HR_ORG_LEVEL5_NAME,
        )
        .select_from(persons)
        .outerjoin(orcids)
        .join(dlcs)
        .where(persons.c.EMAIL_ADDRESS.is_not(None))
        .where(persons.c.LAST_NAME.is_not(None))
        .where(persons.c.KRB_NAME_UPPERCASE.is_not(None))
        .where(persons.c.KRB_NAME_UPPERCASE != "UNKNOWN")
        .where(persons.c.MIT_ID.is_not(None))
        .where(persons.c.ORIGINAL_HIRE_DATE.is_not(None))
        .where(
            persons.c.APPOINTMENT_END_DATE  # noqa: SIM300
            >= datetime(2009, 1, 1)  # noqa: DTZ001
        )
        .where(func.upper(dlcs.c.ORG_HIER_SCHOOL_AREA_NAME).in_(AREAS))
        .where(persons.c.PERSONNEL_SUBAREA_CODE.in_(PS_CODES))
        .where(func.upper(persons.c.JOB_TITLE).in_(TITLES))
    )
    with closing(engine().connect()) as connection:
        result = connection.execute(sql)
        for row in result:
            yield dict(zip(result.keys(), row, strict=True))


class CarbonFtpsTls(FTP_TLS):
    """FTP_TLS subclass with support for SSL session reuse.

    The stdlib version of FTP_TLS creates a new SSL session for data
    transfer commands. This results in a cryptic OpenSSL error message
    when a server requires SSL session reuse. The ntransfercmd here takes
    advantage of the new session parameter to wrap_socket that was added
    in 3.6.

    Additionally, in the stdlib, storbinary destroys the SSL session after
    transfering the file. Since the session has been shared with the
    command connection, OpenSSL will once again generate a cryptic error
    message for subsequent commands. The modified storbinary method here
    removes the unwrap call. Calling quit on the ftp connection should
    still cleanly shutdown the connection.

    Attributes:
        See ftplib.FTP_TLS for more details.
    """

    def ntransfercmd(self, cmd: str, rest: str | int | None = None) -> tuple[socket, int]:
        conn, size = FTP.ntransfercmd(self, cmd, rest)
        if self._prot_p:  # type: ignore[attr-defined]
            conn = self.context.wrap_socket(
                conn, server_hostname=self.host, session=self.sock.session  # type: ignore[union-attr] # noqa: E501
            )
        return conn, size

    def storbinary(
        self,
        cmd: str,
        fp: IO,  # type: ignore[override]
        blocksize: int = 8192,
        callback: Callable | None = None,
        rest: str | None = None,  # type: ignore[override]
    ) -> str:
        self.voidcmd("TYPE I")
        with self.transfercmd(cmd, rest) as conn:
            while 1:
                buf = fp.read(blocksize)
                if not buf:
                    break
                conn.sendall(buf)
                if callback:
                    callback(buf)
        return self.voidresp()


class Writer:
    """A writer that outputs normalized XML strings to a specified file.

    Use this class to generate and output an HR or AA feed.

    Attributes:
        output_file: A file-like object (stream) into which normalized XML
            strings are written.
    """

    def __init__(self, output_file: IO):
        self.output_file = output_file

    def write(self, feed_type: str) -> None:
        """Write the specified feed type to the configured output."""
        if feed_type == "people":
            with person_feed(self.output_file) as f:
                for person in people():
                    f(person)
        elif feed_type == "articles":
            with article_feed(self.output_file) as f:
                for article in articles():
                    f(article)


class PipeWriter(Writer):
    """A read/write carbon.app.Writer for the Symplectic Elements FTP server.

    This class is intended to provide a buffered read/write connecter.

    Attributes:
        output_file: A file-like object (stream) into which normalized XML
            strings are written.
        ftp_output_file: A file-like object (stream) that reads data from
            PipeWriter().output_file and writes its contents to an XML file
            on the Symplectic Elements FTP server.
    """

    def __init__(self, input_file: IO, ftp_output_file: Callable):
        super().__init__(input_file)
        self.ftp_output_file = ftp_output_file

    def write(self, feed_type: str) -> None:
        """Concurrently read/write from the configured inputs and outputs.

        This method will block until both the reader and writer are finished.
        """
        pipe = threading.Thread(target=self.ftp_output_file)
        pipe.start()
        super().write(feed_type)
        self.output_file.close()
        pipe.join()


class FtpFileWriter:
    """A file writer for the Symplectic Elements FTP server.

    The FtpFileWriter will read data from a provided feed and write the contents
    from the feed to a file on the Symplectic Elements FTP server.

    Attributes:
        content_feed: A file-like object (stream) that contains the records
            from the Data Warehouse.
        user: The username for accessing the Symplectic FTP server.
        password: The password for accessing the Symplectic FTP server.
        path: The full file path to the XML file (including the file name) that is
            uploaded to the Symplectic FTP server.
        host: The hostname of the Symplectic FTP server.
        port: The port of the Symplectic FTP server.
    """

    def __init__(
        self,
        content_feed: IO,
        user: str,
        password: str,
        path: str,
        host: str = "localhost",
        port: int = 21,
    ):
        self.content_feed = content_feed
        self.user = user
        self.password = password
        self.path = path
        self.host = host
        self.port = port

    def __call__(self) -> None:
        """Transfer a file using FTP over TLS."""
        ftps = CarbonFtpsTls(timeout=30)
        ftps.connect(host=self.host, port=self.port)
        ftps.login(user=self.user, passwd=self.password)
        ftps.prot_p()
        ftps.storbinary(cmd=f"STOR {self.path}", fp=self.content_feed)
        ftps.quit()


class DatabaseToFtpPipe:
    """A pipe feeding data from the Data Warehouse to the Symplectic Elements FTP server.

    The feed consists of a pipe that connects 'read' and 'write' file-like objects
    (streams) that allows for one-way passing of information to each other. The flow of
    data is as follows:

        1. The records from the Data Warehouse are transformed into normalized
           XML strings and are concurrently written to the 'write' file stream
           one record at a time.

        2. The connected 'read' file stream concurrently transfers data from the
           'write' file stream into an XML file on the Elements FTP server.

    Attributes:
        config: A dictionary of required environment variables for running the feed.
    """

    def __init__(
        self,
        config: dict,
    ):
        self.config = config

    def run(self) -> None:
        read_file, write_file = os.pipe()

        with open(read_file, "rb") as buffered_reader, open(
            write_file, "wb"
        ) as buffered_writer:
            ftp_file = FtpFileWriter(
                content_feed=buffered_reader,
                user=self.config["SYMPLECTIC_FTP_USER"],
                password=self.config["SYMPLECTIC_FTP_PASS"],
                path=self.config["SYMPLECTIC_FTP_PATH"],
                host=self.config["SYMPLECTIC_FTP_HOST"],
                port=int(self.config["SYMPLECTIC_FTP_PORT"]),
            )
            PipeWriter(input_file=buffered_writer, ftp_output_file=ftp_file).write(
                feed_type=self.config["FEED_TYPE"]
            )

    def run_connection_test(self) -> None:
        """Test connection to the Symplectic Elements FTP server.

        Verify that the provided FTP credentials can be used
        to successfully connect to the Symplectic Elements FTP server.
        """
        logger.info("Testing connection to the Symplectic Elements FTP server")
        try:
            ftps = CarbonFtpsTls(timeout=30)
            ftps.connect(
                host=self.config["SYMPLECTIC_FTP_HOST"],
                port=int(self.config["SYMPLECTIC_FTP_PORT"]),
            )
            ftps.login(
                user=self.config["SYMPLECTIC_FTP_USER"],
                passwd=self.config["SYMPLECTIC_FTP_PASS"],
            )
        except Exception as error:
            error_message = (
                f"Failed to connect to the Symplectic Elements FTP server: {error}"
            )
            logger.exception(error_message)
        else:
            logger.info("Successfully connected to the Symplectic Elements FTP server")
            ftps.quit()
