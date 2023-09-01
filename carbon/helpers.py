import logging
from datetime import UTC, datetime
from typing import Any

import boto3

logger = logging.getLogger(__name__)


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
