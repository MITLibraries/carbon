import pytest

from carbon.db import DatabaseEngine


def test_nonconfigured_engine_raises_attributeerror():
    nonconfigured_engine = DatabaseEngine()

    with pytest.raises(AttributeError):
        nonconfigured_engine()
