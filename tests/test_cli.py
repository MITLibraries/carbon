# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os

from click.testing import CliRunner
from lxml import etree as ET
import pytest

from carbon.cli import main


pytestmark = pytest.mark.usefixtures('load_data')


@pytest.fixture
def runner():
    return CliRunner()


def test_people_returns_people(runner, xml_data):
    res = runner.invoke(main, ['--db', 'sqlite://', '-o', '-', 'people'])
    assert res.exit_code == 0
    assert res.stdout_bytes == \
        ET.tostring(xml_data, encoding="UTF-8", xml_declaration=True)


def test_articles_returns_articles(runner, articles_data):
    res = runner.invoke(main, ['--db', 'sqlite://', '-o', '-', 'articles'])
    assert res.exit_code == 0
    assert res.stdout_bytes == \
        ET.tostring(articles_data, encoding='UTF-8', xml_declaration=True)


def test_file_is_ftped(runner, xml_data, ftp_server):
    s, d = ftp_server
    res = runner.invoke(main, ['--db', 'sqlite://', '--ftp', '--ftp-port',
                               s[1], '--ftp-user', 'user', '--ftp-pass',
                               'pass', '--ftp-path', '/peeps.xml', 'people'])
    assert res.exit_code == 0
    xml = ET.parse(os.path.join(d, 'peeps.xml'))
    xp = xml.xpath("/s:records/s:record/s:field[@name='[FirstName]']",
                   namespaces={'s': 'http://www.symplectic.co.uk/hrimporter'})
    assert xp[1].text == 'Þorgerðr'
