import pytest
from anicli_api.random_useragent import Agent


@pytest.mark.parametrize("agent1,agent2", [(Agent.mobile(), Agent.mobile()),
                                           (Agent.desktop(), Agent.desktop()),
                                           (Agent.random(), Agent.random()),
                                           (Agent.desktop(), Agent.mobile()),
                                           (Agent.random(), Agent.mobile()),
                                           (Agent.random(), Agent.desktop())])
def test_fake_agent(agent1: str, agent2: str):
    assert agent1 != agent2
