"""Verify single-agent behavior is unchanged after multi-agent extension."""

from src.config.models import AgentConfig
from src.config.loader import ConfigLoader


def test_single_agent_defaults():
    """Single agent without kind field should default to single."""
    agent = AgentConfig(id="test", name="Test")
    assert agent.kind == "single"
    assert agent.members is None
    assert agent.workflows is None


def test_single_agent_loads_correctly():
    """Existing single-agent YAML should still parse correctly."""
    loader = ConfigLoader()
    agent = loader.load_single_agent("default", "travel_agent")

    assert agent is not None
    assert agent.kind == "single"
