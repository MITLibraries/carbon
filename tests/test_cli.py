# -*- coding: utf-8 -*-
from __future__ import absolute_import
from io import BytesIO

from click.testing import CliRunner
from lxml import etree as ET
import pytest

from carbon.cli import main


pytestmark = pytest.mark.usefixtures('load_data')


@pytest.fixture
def runner():
    return CliRunner()


def test_feed_returns_people(runner, E, xml_data):
    b = BytesIO()
    res = runner.invoke(main, ['-o', b, 'sqlite://'])
    assert res.exit_code == 0
    assert b.getvalue() == \
        ET.tostring(xml_data, encoding="UTF-8", xml_declaration=True)
