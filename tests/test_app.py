# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pytest

from carbon import people


pytestmark = pytest.mark.usefixtures('load_data')


def test_people_generates_people():
    peeps = people()
    person = next(peeps)
    assert person['KRB_NAME'] == 'foobar'
    person = next(peeps)
    assert person['KRB_NAME'] == 'foobaz'
