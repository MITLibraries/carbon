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


def test_load_returns_people(runner, E):
    xml = E.records(
        E.record(
            E.field('123456', name='[Proprietary_ID]'),
            E.field('foobar', name='[Username]')
        ),
        E.record(
            E.field('098754', name='[Proprietary_ID]'),
            E.field('foobaz', name='[Username]')
        )
    )
    res = runner.invoke(main, ['load', '--db',
                        'sqlite:///tests/db/test.db'])
    assert res.exit_code == 0
    assert res.output.encode('utf-8') == ET.tostring(xml) + b'\n'
