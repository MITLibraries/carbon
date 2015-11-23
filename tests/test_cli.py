# -*- coding: utf-8 -*-
from __future__ import absolute_import

from click.testing import CliRunner
import pytest

from carbon.cli import main


pytestmark = pytest.mark.usefixtures('load_data')


@pytest.fixture
def runner():
    return CliRunner()


def test_load_returns_people(runner):
    res = runner.invoke(main, ['load', '--db',
                        'sqlite:///tests/db/test.db'])
    assert res.exit_code == 0
    assert 'foobar' in res.output
