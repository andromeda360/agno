import uuid

from agno_v2.agent.agent import Agent
from agno_v2.team.team import Team
from agno_v2.utils.team import get_member_id


def test_get_member_id():
    member = Agent(name="Test Agent")
    assert get_member_id(member) == "test-agent"
    member = Agent(name="Test Agent", id="123")
    assert get_member_id(member) == "123"
    member = Agent(name="Test Agent", id=str(uuid.uuid4()))
    assert get_member_id(member) == "test-agent"
    member = Agent(id=str(uuid.uuid4()))
    assert get_member_id(member) == member.id

    member = Agent(name="Test Agent")
    inner_team = Team(name="Test Team", members=[member])
    assert get_member_id(inner_team) == "test-team"
    inner_team = Team(name="Test Team", id="123", members=[member])
    assert get_member_id(inner_team) == "123"
    inner_team = Team(name="Test Team", id=str(uuid.uuid4()), members=[member])
    assert get_member_id(inner_team) == "test-team"
    inner_team = Team(id=str(uuid.uuid4()), members=[member])
    assert get_member_id(inner_team) == inner_team.id
