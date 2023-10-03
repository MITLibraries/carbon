import logging
from typing import Any

from sqlalchemy import (
    Column,
    Date,
    Engine,
    ForeignKey,
    MetaData,
    Numeric,
    String,
    Table,
    Unicode,
    UnicodeText,
    create_engine,
)
from sqlalchemy.exc import DatabaseError

logger = logging.getLogger(__name__)

metadata = MetaData()

persons = Table(
    "HR_PERSON_EMPLOYEE_LIMITED",
    metadata,
    Column("MIT_ID", String),
    Column("KRB_NAME_UPPERCASE", String),
    Column("FIRST_NAME", Unicode),
    Column("LAST_NAME", Unicode),
    Column("MIDDLE_NAME", Unicode),
    Column("EMAIL_ADDRESS", String),
    Column("DATE_TO_FACULTY", Date),
    Column("ORIGINAL_HIRE_DATE", Date),
    Column("APPOINTMENT_END_DATE", Date),
    Column("PERSONNEL_SUBAREA_CODE", String),
    Column("JOB_TITLE", String),
    Column("HR_ORG_UNIT_ID", String),
)

dlcs = Table(
    "HR_ORG_UNIT",
    metadata,
    Column(
        "HR_ORG_UNIT_ID",
        String,
        ForeignKey("HR_PERSON_EMPLOYEE_LIMITED.HR_ORG_UNIT_ID"),
    ),
    Column("ORG_HIER_SCHOOL_AREA_NAME", String),
    Column("DLC_NAME", String),
    Column("HR_ORG_LEVEL5_NAME", String),
)

orcids = Table(
    "ORCID_TO_MITID",
    metadata,
    Column("MIT_ID", String, ForeignKey("HR_PERSON_EMPLOYEE_LIMITED.MIT_ID")),
    Column("ORCID", String),
)

aa_articles = Table(
    "AA_ARTICLE",
    metadata,
    Column("AA_MATCH_SCORE", Numeric(3, 1)),
    Column("ARTICLE_ID", String),
    Column("ARTICLE_TITLE", Unicode),
    Column("ARTICLE_YEAR", String),
    Column("AUTHORS", UnicodeText),
    Column("DOI", String),
    Column("ISSN_ELECTRONIC", String),
    Column("ISSN_PRINT", String),
    Column("IS_CONFERENCE_PROCEEDING", String),
    Column("JOURNAL_FIRST_PAGE", String),
    Column("JOURNAL_LAST_PAGE", String),
    Column("JOURNAL_ISSUE", Unicode),
    Column("JOURNAL_NAME", Unicode),
    Column("JOURNAL_VOLUME", Unicode),
    Column("MIT_ID", String),
    Column("PUBLISHER", Unicode),
)


class DatabaseEngine:
    """Database engine.

    This provides access to an SQLAlchemy database engine. Only one
    of these should be created per application. Calling the object
    will return the configured engine, though you should generally
    use the :func:`~carbon.db.session` to interact with the databse.
    """

    _engine = None

    def __call__(self) -> Engine:
        if self._engine:
            return self._engine

        nonconfigured_engine_error_message = (
            "No SQLAlchemy engine was found. The engine must be created "
            "by running 'engine.configure()' with a valid connection string."
        )
        raise AttributeError(nonconfigured_engine_error_message)

    def configure(self, connection_string: str, **kwargs: Any) -> None:  # noqa: ANN401
        self._engine = self._engine or create_engine(connection_string, **kwargs)

    def run_connection_test(self) -> None:
        """Test connection to the Data Warehouse.

        Verify that the provided Data Warehouse credentials can be used
        to successfully connect to the Data Warehouse.
        """
        logger.info("Testing connection to the Data Warehouse")
        try:
            connection = self._engine.connect()  # type: ignore[union-attr]
        except DatabaseError as error:
            error_message = f"Failed to connect to the Data Warehouse: {error}"
            logger.error(error_message)  # noqa: TRY400
            raise
        except Exception as error:
            error_message = f"Failed to connect to the Data Warehouse: {error}"
            logger.exception(error_message)
            raise
        else:
            dbapi_connection = connection.connection
            version = (
                dbapi_connection.version if hasattr(dbapi_connection, "version") else ""
            )
            logger.info(
                "Successfully connected to the Data Warehouse: %s",
                version,  # type: ignore[union-attr]
            )
            connection.close()
