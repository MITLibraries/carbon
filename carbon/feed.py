from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import closing
from datetime import datetime
from typing import IO, Any, ClassVar

from lxml import etree as ET
from sqlalchemy import func, select
from sqlalchemy.sql.selectable import Select

from carbon.database import DatabaseEngine, aa_articles, dlcs, orcids, persons
from carbon.helpers import (
    get_group_name,
    get_hire_date_string,
    get_initials,
)


class BaseXmlFeed(ABC):
    """Base XML feed class.

    This is the abstract class for creating XML feeds. The following class attributes
    are unique per subclass of carbon.feed.BaseXmlFeed:

        root_element_name: The 'tag' assigned to the root Element.
        query: The select statmenet submitted to the Data Warehouse to retrieve records.

    Attributes:
        engine: A configured carbon.database.DatabaseEngine that can connect to the
            Data Warehouse.
        output_file: A file-like object (stream) into which normalized XML strings
            strings are written.

    """

    root_element_name: str = ""
    query: Select = select()
    processed_record_count: int = 0

    def __init__(self, engine: DatabaseEngine, output_file: IO):
        self.engine = engine
        self.output_file = output_file

    @property
    def records(self) -> Generator[dict[str, Any], Any, None]:
        """Create a generator of 'people' or 'article' records from the Data Warehouse.

        Yields:
            Generator[dict[str, Any], Any, None]: Records that
                match the query submitted to the Data Warehouse.
        """
        with closing(self.engine().connect()) as connection:
            result = connection.execute(self.query)
            for row in result:
                yield dict(zip(result.keys(), row, strict=True))

    @abstractmethod
    def _add_element(self, record: dict[str, Any]) -> None | ET._Element:
        """Create an XML element for a provided record.

        Must be overridden by subclasses.

        Args:
            record (dict[str, Any]): A record matching the query submitted to
                the Data Warehouse.

        Returns:
            None | ET._Element: A record XML element.
        """

    def _add_subelement(
        self,
        parent: ET._Element,
        element_name: str,
        element_text: str | None = None,
        **kwargs: str,
    ) -> ET._Element:
        """Add an XML subelement to an existing element.

        Args:
            parent (ET._Element): The parent element.
            element_name (str): The name of the subelement.
            element_text (str | None, optional): The value stored in the subelement.
                Defaults to None.
            **kwargs (str): Keyword arguments representing attributes for the subelement.
                The 'name' argument is set for 'people' elements.

        Returns:
            ET._Element: A subelement with text.
        """
        subelement = ET.SubElement(parent, element_name, attrib=kwargs)
        subelement.text = element_text
        return subelement

    def run(self, **kwargs: dict[str, Any]) -> None:
        """Generate a feed that streams normalized XML strings to an XML file."""
        with ET.xmlfile(self.output_file, encoding="UTF-8") as xml_file:
            xml_file.write_declaration()
            with xml_file.element(tag=self.root_element_name, **kwargs):
                for record in self.records:
                    element = self._add_element(record)
                    xml_file.write(element)
                    self.processed_record_count += 1


class ArticlesXmlFeed(BaseXmlFeed):
    """Articles XML feed class."""

    root_element_name = "ARTICLES"
    query = (
        select(aa_articles)
        .where(aa_articles.c.ARTICLE_ID.is_not(None))
        .where(aa_articles.c.ARTICLE_TITLE.is_not(None))
        .where(aa_articles.c.DOI.is_not(None))
        .where(aa_articles.c.MIT_ID.is_not(None))
    )

    def _add_element(self, record: dict[str, Any]) -> ET._Element:
        """Create an XML element representing an article.

        The function will create a single 'ARTICLE' element that contains subelements
        representing fields in a record from the 'AA_ARTICLE table'.

        Args:
            record (dict[str, Any]): A record matching the query submitted to the
                Data Warehouse for retrieving 'articles' records.

        Returns:
            ET._Element: An articles XML element.
        """
        article = ET.Element("ARTICLE")
        self._add_subelement(article, "AA_MATCH_SCORE", str(record["AA_MATCH_SCORE"]))
        self._add_subelement(article, "ARTICLE_ID", record["ARTICLE_ID"])
        self._add_subelement(article, "ARTICLE_TITLE", record["ARTICLE_TITLE"])
        self._add_subelement(article, "ARTICLE_YEAR", record["ARTICLE_YEAR"])
        self._add_subelement(article, "AUTHORS", record["AUTHORS"])
        self._add_subelement(article, "DOI", record["DOI"])
        self._add_subelement(article, "ISSN_ELECTRONIC", record["ISSN_ELECTRONIC"])
        self._add_subelement(article, "ISSN_PRINT", record["ISSN_PRINT"])
        self._add_subelement(
            article, "IS_CONFERENCE_PROCEEDING", record["IS_CONFERENCE_PROCEEDING"]
        )
        self._add_subelement(article, "JOURNAL_FIRST_PAGE", record["JOURNAL_FIRST_PAGE"])
        self._add_subelement(article, "JOURNAL_LAST_PAGE", record["JOURNAL_LAST_PAGE"])
        self._add_subelement(article, "JOURNAL_ISSUE", record["JOURNAL_ISSUE"])
        self._add_subelement(article, "JOURNAL_VOLUME", record["JOURNAL_VOLUME"])
        self._add_subelement(article, "JOURNAL_NAME", record["JOURNAL_NAME"])
        self._add_subelement(article, "MIT_ID", record["MIT_ID"])
        self._add_subelement(article, "PUBLISHER", record["PUBLISHER"])
        return article


class PeopleXmlFeed(BaseXmlFeed):
    """People XML feed class.

    There are several class attributes that are required only for the 'people' XML feed:

        areas, ps_codes, title: A series of tuples containing strings used in
            carbon.feed.PeopleXmlFeed.query.
        symplectic_elements_namespace: The namespace assigned to the 'xmlns'
            attribute of the root 'records' element.
        namespace_mapping: A configuration required to clean up the 'xmlns'
            attribute of the root 'records' element when serialized.
    """

    areas: tuple[str, ...] = (
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
    ps_codes: tuple[str, ...] = (
        "CFAN",
        "CFAT",
        "CFEL",
        "CSRS",
        "CSRR",
        "COAC",
        "COAR",
        "L303",
    )
    titles: tuple[str, ...] = (
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

    symplectic_elements_namespace: str = "http://www.symplectic.co.uk/hrimporter"
    namespace_mapping: ClassVar[dict] = {None: symplectic_elements_namespace}

    root_element_name: str = str(ET.QName(symplectic_elements_namespace, tag="records"))
    query = (
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
        .where(func.upper(dlcs.c.ORG_HIER_SCHOOL_AREA_NAME).in_(areas))
        .where(persons.c.PERSONNEL_SUBAREA_CODE.in_(ps_codes))
        .where(func.upper(persons.c.JOB_TITLE).in_(titles))
    )

    def _add_element(self, record: dict[str, Any]) -> ET._Element:
        """Create an XML element representing a person.

        The function will create a single 'record' element that contains subelements
        representing fields from the 'HR_PERSON_EMPLOYEE_LIMITED', 'HR_ORG_UNIT',
        and 'ORCID_TO_MITID' tables.

        Args:
            record (dict[str, Any]): A record matching the query submitted to the
                Data Warehouse for retrieving 'people' records.

        Returns:
            ET._Element: A person XML element.
        """
        person = ET.Element("record")
        self._add_subelement(person, "field", record["MIT_ID"], name="[Proprietary_ID]")
        self._add_subelement(
            person, "field", record["KRB_NAME_UPPERCASE"], name="[Username]"
        )
        self._add_subelement(
            person,
            "field",
            get_initials(record["FIRST_NAME"], record["MIDDLE_NAME"]),
            name="[Initials]",
        )
        self._add_subelement(person, "field", record["LAST_NAME"], name="[LastName]")
        self._add_subelement(person, "field", record["FIRST_NAME"], name="[FirstName]")
        self._add_subelement(person, "field", record["EMAIL_ADDRESS"], name="[Email]")
        self._add_subelement(person, "field", "MIT", name="[AuthenticatingAuthority]")
        self._add_subelement(person, "field", "1", name="[IsAcademic]")
        self._add_subelement(person, "field", "1", name="[IsCurrent]")
        self._add_subelement(person, "field", "1", name="[LoginAllowed]")
        self._add_subelement(
            person,
            "field",
            get_group_name(record["DLC_NAME"], record["PERSONNEL_SUBAREA_CODE"]),
            name="[PrimaryGroupDescriptor]",
        )
        self._add_subelement(
            person,
            "field",
            get_hire_date_string(record["ORIGINAL_HIRE_DATE"], record["DATE_TO_FACULTY"]),
            name="[ArriveDate]",
        )
        self._add_subelement(
            person,
            "field",
            record["APPOINTMENT_END_DATE"].strftime("%Y-%m-%d"),
            name="[LeaveDate]",
        )
        self._add_subelement(person, "field", record["ORCID"], name="[Generic01]")
        self._add_subelement(
            person, "field", record["PERSONNEL_SUBAREA_CODE"], name="[Generic02]"
        )
        self._add_subelement(
            person, "field", record["ORG_HIER_SCHOOL_AREA_NAME"], name="[Generic03]"
        )
        self._add_subelement(person, "field", record["DLC_NAME"], name="[Generic04]")
        self._add_subelement(
            person, "field", record.get("HR_ORG_LEVEL5_NAME"), name="[Generic05]"
        )
        return person
