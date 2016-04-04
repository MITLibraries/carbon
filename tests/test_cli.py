# -*- coding: utf-8 -*-
from __future__ import absolute_import

from click.testing import CliRunner
from lxml import etree as ET
import pytest

from carbon.cli import main


pytestmark = pytest.mark.usefixtures('load_data')


@pytest.fixture
def runner():
    return CliRunner()


def test_people_returns_people(runner, xml_data):
    res = runner.invoke(main, ['sqlite://', 'people'])
    assert res.exit_code == 0
    assert res.output_bytes == \
        ET.tostring(xml_data, encoding="UTF-8", xml_declaration=True)


def test_articles_returns_articles(runner, articles_data):
    res = runner.invoke(main, ['sqlite://', 'articles'])
    assert res.exit_code == 0
    assert res.output_bytes == \
        ET.tostring(articles_data, encoding='UTF-8', xml_declaration=True)
