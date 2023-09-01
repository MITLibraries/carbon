import logging
import re
from datetime import UTC, datetime
from typing import Any

import boto3

logger = logging.getLogger(__name__)


def group_name(dlc: str, sub_area: str) -> str:
    qualifier = "Faculty" if sub_area in ("CFAT", "CFAN") else "Non-faculty"
    return f"{dlc} {qualifier}"


def hire_date_string(original_start_date: datetime, date_to_faculty: datetime) -> str:
    if date_to_faculty:
        return date_to_faculty.strftime("%Y-%m-%d")
    return original_start_date.strftime("%Y-%m-%d")


def initialize_part(name: str) -> str:
    """Turn a name part into uppercased initials.

    This function will do its best to parse the argument into one or
    more initials. The first step is to remove any character that is
    not alphanumeric, whitespace or a hyphen. The remaining string
    is split on word boundaries, retaining both the words and the
    boundaries. The first character of each list member is then
    joined together, uppercased and returned.

    Some examples::

        assert initialize_part('Foo Bar') == 'F B'
        assert initialize_part('F. Bar-Baz') == 'F B-B'
        assert initialize_part('Foo-bar') == 'F-B'
        assert initialize_part(u'влад') == u'В'

    """  # noqa: RUF002
    name = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE)
    return "".join([x[:1] for x in re.split(r"(\W+)", name, flags=re.UNICODE)]).upper()


def initials(*args: str) -> str:
    """Turn `*args` into a space-separated string of initials.

    Each argument is processed through :func:`~initialize_part` and
    the resulting list is joined with a space.
    """
    return " ".join([initialize_part(n) for n in args if n])


def sns_log(
    config_values: dict[str, Any], status: str, error: Exception | None = None
) -> None:
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
