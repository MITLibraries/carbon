import logging
import re
from datetime import UTC, datetime
from typing import Any

import boto3

logger = logging.getLogger(__name__)


def _convert_to_initials(name_component: str) -> str:
    """Turn a name component into uppercased initials.

    This function will do its best to parse the argument into one or
    more initials. The first step is to remove any character that is
    not alphanumeric, whitespace or a hyphen. The remaining string
    is split on word boundaries, retaining both the words and the
    boundaries. The first character of each list member is then
    joined together, uppercased and returned.

    Some examples::

        assert _convert_to_initials('Foo Bar') == 'F B'
        assert _convert_to_initials('F. Bar-Baz') == 'F B-B'
        assert _convert_to_initials('Foo-bar') == 'F-B'
        assert _convert_to_initials(u'влад') == u'В'

    """  # noqa: RUF002
    name_component = re.sub(r"[^\w\s-]", "", name_component, flags=re.UNICODE)
    return "".join(
        [x[:1] for x in re.split(r"(\W+)", name_component, flags=re.UNICODE)]
    ).upper()


def get_group_name(dlc: str, sub_area: str) -> str:
    """Create a primary group name for a 'people' record.

    Args:
        dlc (str): The value for the 'DLC_NAME' field from a 'people' record.
        sub_area (str): The value for the 'PERSONNEL_SUB_AREA_CODE' field from a
            'people' record.

    Returns:
        str: A group name for a 'people' record, consisting of the DLC name and a flag
            indicating 'Faculty' or 'Non-faculty'.
    """
    qualifier = "Faculty" if sub_area in ("CFAT", "CFAN") else "Non-faculty"
    return f"{dlc} {qualifier}"


def get_hire_date_string(original_start_date: datetime, date_to_faculty: datetime) -> str:
    """Create a string indicating the hire date for a 'people' record.

    If the record has a value for the 'DATE_TO_FACULTY' field, this value is used;
    if not, the value for the 'ORIGINAL_HIRE_DATE' field is used. Dates are formatted
    as: YYYY-MM-DD (i.e., 2023-01-01).

    Args:
        original_start_date (datetime): The value for the 'ORIGINAL_HIRE_DATE' field
            from a 'people' record.
        date_to_faculty (datetime): The value for the 'DATE_TO_FACULTY field from a
            'people' record.

    Returns:
        str: The hire date formatted as a string.
    """
    if date_to_faculty:
        return date_to_faculty.strftime("%Y-%m-%d")
    return original_start_date.strftime("%Y-%m-%d")


def get_initials(*args: str) -> str:
    """Convert a tuple of name components into a space-separated string of initials.

    Each name component is processed through helpers.get_initials() and
    the resulting list is joined with a space.

    Returns:
        str: A string containing the initials of the provided name components.
    """
    return " ".join(
        [
            _convert_to_initials(name_component)
            for name_component in args
            if name_component
        ]
    )


def sns_log(
    config_values: dict[str, Any], status: str, error: Exception | None = None
) -> None:
    """Send a message to an Amazon SNS topic about the status of the Carbon run.

    When Carbon is run in the 'stage' environment, subscribers to the 'carbon-ecs-stage'
    topic receive an email with the published message. For a given run, two messages are
    published:

        1. When status = 'start', a message indicating the Carbon run has started.
        2. When status = 'start'/'fail', a message indicating if the Carbon run has
            successfully completed or encountered an error.

    Args:
        config_values (dict[str, Any]): A dictionary of required environment variables
          for running the feed.
        status (str): The status of the Carbon run that is used to determine the message
          published by SNS. The following values are accepted: 'start', 'success',
          and 'fail'.
        error (Exception | None, optional): The exception thrown for a failed Carbon run.
          Defaults to None.
    """
    sns_client = boto3.client("sns")
    sns_id = config_values.get("SNS_TOPIC")
    stage = config_values.get("SYMPLECTIC_FTP_PATH", "").lstrip("/").split("/")[0]
    feed = config_values.get("FEED_TYPE", "")

    if status == "start":
        sns_client.publish(
            TopicArn=sns_id,
            Subject="Carbon run",
            Message=(
                f"[{datetime.now(tz=UTC).isoformat()}] Starting carbon run for the "
                f"{feed} feed in the {stage} environment."
            ),
        )
    elif status == "success":
        sns_client.publish(
            TopicArn=sns_id,
            Subject="Carbon run",
            Message=(
                f"[{datetime.now(tz=UTC).isoformat()}] Finished carbon run for the "
                f"{feed} feed in the {stage} environment."
            ),
        )
        logger.info("Carbon run has successfully completed.")
    elif status == "fail":
        sns_client.publish(
            TopicArn=sns_id,
            Subject="Carbon run",
            Message=(
                f"[{datetime.now(tz=UTC).isoformat()}] The following problem was "
                f"encountered during the carbon run for the {feed} feed "
                f"in the {stage} environment: {error}."
            ),
        )
        logger.info("Carbon run has failed.")
