from __future__ import annotations

import logging
import os
import threading
from ftplib import FTP, FTP_TLS  # nosec
from typing import IO, TYPE_CHECKING

from carbon.feed import ArticlesXmlFeed, PeopleXmlFeed

if TYPE_CHECKING:
    from collections.abc import Callable
    from socket import socket

    from carbon.database import DatabaseEngine

logger = logging.getLogger(__name__)


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
        """Initiate a transfer over the data connection."""
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
        """Store a file in binary mode."""
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


class FileWriter:
    """A writer that outputs normalized XML strings to a specified file.

    Use this class to generate either a 'people' or 'articles' feed that is written
    to a specified output file.

    Attributes:
        output_file: A file-like object (stream) into which normalized XML
            strings are written.
    """

    def __init__(self, engine: DatabaseEngine, output_file: IO):
        self.output_file = output_file
        self.engine = engine

    def write(self, feed_type: str) -> None:
        """Write the specified feed type to the configured output."""
        xml_feed: PeopleXmlFeed | ArticlesXmlFeed
        if feed_type == "people":
            xml_feed = PeopleXmlFeed(engine=self.engine, output_file=self.output_file)
            xml_feed.run(nsmap=xml_feed.namespace_mapping)
        elif feed_type == "articles":
            xml_feed = ArticlesXmlFeed(engine=self.engine, output_file=self.output_file)
            xml_feed.run()
        logger.info(
            "The feed has collected %s '%s' records", xml_feed.record_count, feed_type
        )


class ConcurrentFtpFileWriter(FileWriter):
    """A read/write carbon.app.Writer for the Symplectic Elements FTP server.

    This class is intended to provide a buffered read/write connecter.

    Attributes:
        output_file: A file-like object (stream) into which normalized XML
            strings are written.
        ftp_output_file: A file-like object (stream) that reads data from
            PipeWriter().output_file and writes its contents to an XML file
            on the Symplectic Elements FTP server.
    """

    def __init__(self, engine: DatabaseEngine, input_file: IO, ftp_output_file: Callable):
        super().__init__(engine, input_file)
        self.ftp_output_file = ftp_output_file

    def write(self, feed_type: str) -> None:
        """Concurrently read/write from the configured inputs and outputs.

        This method will block until both the reader and writer are finished.
        """
        thread = threading.Thread(target=self.ftp_output_file)
        thread.start()
        super().write(feed_type)
        self.output_file.close()
        thread.join()


class FtpFile:
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


class DatabaseToFilePipe:
    """A pipe feeding data from the Data Warehouse to a local file."""

    def __init__(self, config: dict, engine: DatabaseEngine, output_file: IO):
        self.config = config
        self.engine = engine
        self.output_file = output_file

    def run(self) -> None:
        FileWriter(engine=self.engine, output_file=self.output_file).write(
            feed_type=self.config["FEED_TYPE"]
        )


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

    def __init__(self, config: dict, engine: DatabaseEngine):
        self.config = config
        self.engine = engine

    def run(self) -> None:
        read_file, write_file = os.pipe()

        with open(read_file, "rb") as buffered_reader, open(
            write_file, "wb"
        ) as buffered_writer:
            ftp_file = FtpFile(
                content_feed=buffered_reader,
                user=self.config["SYMPLECTIC_FTP_USER"],
                password=self.config["SYMPLECTIC_FTP_PASS"],
                path=self.config["SYMPLECTIC_FTP_PATH"],
                host=self.config["SYMPLECTIC_FTP_HOST"],
                port=int(self.config["SYMPLECTIC_FTP_PORT"]),
            )
            ConcurrentFtpFileWriter(
                engine=self.engine, input_file=buffered_writer, ftp_output_file=ftp_file
            ).write(feed_type=self.config["FEED_TYPE"])

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
            raise
        else:
            logger.info("Successfully connected to the Symplectic Elements FTP server")
            ftps.quit()
