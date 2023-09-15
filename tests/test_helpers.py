from unittest.mock import patch

from freezegun import freeze_time

from carbon.config import load_config_values
from carbon.helpers import get_group_name, get_initials, sns_log


def test_group_name_adds_faculty():
    assert get_group_name("FOOBAR", "CFAT") == "FOOBAR Faculty"
    assert get_group_name("FOOBAR", "CFAN") == "FOOBAR Faculty"


def test_group_name_adds_non_faculty():
    assert get_group_name("FOOBAR", "COAC") == "FOOBAR Non-faculty"


def test_initials_returns_first_and_middle():
    assert get_initials("Foo", "Bar") == "F B"
    assert get_initials("Foo") == "F"
    assert get_initials("F", "B") == "F B"
    assert get_initials("Foo-bar", "Gaz") == "F-B G"
    assert get_initials("Foo Bar-baz", "G") == "F B-B G"
    assert get_initials("Foo", "") == "F"
    assert get_initials("Foo", None) == "F"
    assert get_initials("Gull-Þóris") == "G-Þ"
    assert get_initials("владимир", "ильич", "ленин") == "В И Л"  # noqa: RUF001
    assert get_initials("F. M.", "Laxdæla") == "F M L"


@freeze_time("2023-08-18")
def test_sns_log_publishes_status_messages(stubbed_sns_client):
    config_values = load_config_values()
    with patch("boto3.client") as mocked_boto_client:
        mocked_boto_client.return_value = stubbed_sns_client
        sns_start_response = sns_log(config_values, status="start")
        assert sns_start_response["MessageId"] == "StartMessageId"

        sns_success_response = sns_log(config_values, status="success")
        assert sns_success_response["MessageId"] == "SuccessMessageId"

        sns_fail_response = sns_log(config_values, status="fail")
        assert sns_fail_response["MessageId"] == "FailMessageId"
