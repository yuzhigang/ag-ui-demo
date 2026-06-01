"""End-to-end test: verify travel_group can be loaded and built."""

from src.config.loader import ConfigLoader


def test_load_travel_group_config():
    """Verify travel_group.yaml is parsed as kind: multi."""
    loader = ConfigLoader()
    agent = loader.load_single_agent("default", "travel_group")

    assert agent is not None
    assert agent.kind == "multi"
    assert len(agent.members) == 3
    assert len(agent.workflows) == 1
    assert agent.workflows[0].id == "full_plan"
    assert agent.workflows[0].graph.start == ["weather_agent"]
    assert agent.workflows[0].graph.end == ["flight_agent"]
    assert len(agent.workflows[0].graph.edges) == 2


def test_load_member_agents():
    """Verify member agent configs can be loaded."""
    loader = ConfigLoader()

    weather = loader.load_single_agent("default", "weather_agent")
    assert weather is not None
    assert weather.id == "weather_agent"
    assert weather.kind == "single"

    hotel = loader.load_single_agent("default", "hotel_agent")
    assert hotel is not None
    assert hotel.id == "hotel_agent"
