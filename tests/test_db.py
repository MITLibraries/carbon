import pytest

from carbon.database import DatabaseEngine


def test_nonconfigured_engine_raises_attributeerror():
    nonconfigured_engine = DatabaseEngine()

    with pytest.raises(AttributeError):
        nonconfigured_engine()
