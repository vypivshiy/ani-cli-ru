from typing import Pattern
import re

import pytest

from anicli_ru.utils import BasePatternModel, Field
from anicli_ru.utils import Agent


class TestPattern(BasePatternModel):
    foo: Field[int, Pattern] = int, re.compile(r"foo=(.*)")
    bar: Field[int, Pattern] = int, re.compile(r"bar=(.*)")
    baz: Field[int, Pattern] = int, re.compile(r"baz=(.*)")
    IGNORE_VALUE: bool = True
    not_ignored_value: bool = False


@pytest.mark.parametrize("agent1,agent2", [(Agent.mobile(), Agent.mobile()),
                                           (Agent.desktop(), Agent.desktop()),
                                           (Agent.random(), Agent.random()),
                                           (Agent.desktop(), Agent.mobile()),
                                           (Agent.random(), Agent.mobile()),
                                           (Agent.random(), Agent.desktop())])
def test_fake_agent(agent1: str, agent2: str):
    assert agent1 != agent2


def test_pattern_model():
    dct = TestPattern.to_dict("""foo=100\nbar=200\nbaz=300\nanystranystranystraaaaa....""")
    assert dct.get("IGNORE_VALUE") is None
    assert dct == {'foo': '100', 'bar': '200', 'baz': '300', 'not_ignored_value': False}
