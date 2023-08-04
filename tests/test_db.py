import pytest

from carbon.db import DatabaseEngine


def test_nonconfigured_engine():
    nonconfigured_engine = DatabaseEngine()

    with pytest.raises(AttributeError):
        nonconfigured_engine()
