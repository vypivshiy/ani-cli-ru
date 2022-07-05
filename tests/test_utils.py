import pytest

from tests.fixtures.fake_extractor import FakeParser, FakeJsonParser  # type: ignore
from anicli_ru.utils import Agent


@pytest.mark.parametrize("agent1,agent2", [(Agent.mobile(), Agent.mobile()),
                                           (Agent.desktop(), Agent.desktop()),
                                           (Agent.random(), Agent.random()),
                                           (Agent.desktop(), Agent.mobile()),
                                           (Agent.random(), Agent.mobile()),
                                           (Agent.random(), Agent.desktop())])
def test_fake_agent(agent1: str, agent2: str):
    assert agent1 != agent2
