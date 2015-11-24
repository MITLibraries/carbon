# -*- coding: utf-8 -*-
from __future__ import absolute_import

from click.testing import CliRunner
from lxml import etree as ET
import pytest
import requests_mock

from carbon.cli import main


pytestmark = pytest.mark.usefixtures('load_data')


@pytest.fixture
def runner():
    return CliRunner()


def test_load_returns_people(runner, E, xml_data):
    res = runner.invoke(main, ['load', 'sqlite:///tests/db/test.db'])
    assert res.exit_code == 0
    assert res.output.encode('utf-8') == \
        ET.tostring(xml_data, encoding="UTF-8", xml_declaration=True) + b'\n'


def test_load_posts_to_url(runner, E, xml_data):
    with requests_mock.Mocker() as m:
        m.post('http://example.com', text='congrats')
        runner.invoke(main, ['load', 'sqlite:///tests/db/test.db', '--url',
                             'http://example.com'])
        req = m.request_history[0]
        assert req.text.encode('utf-8') == ET.tostring(xml_data,
                                                       encoding="UTF-8",
                                                       xml_declaration=True)
