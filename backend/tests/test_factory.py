"""Tests for Agent factory."""

from unittest.mock import MagicMock, patch

from src.config.models import ModelConfig, ResolvedAgentConfig, ToolConfig
from src.config.registry import ResourceRegistry
from src.factory import AgentFactory


class TestAgentFactory:
    @patch("src.factory.importlib.import_module")
    def test_resolve_tools(self, mock_import):
        def mock_get_weather(city, date):
            return {"city": city}
        mock_get_weather.__name__ = "get_weather"

        mock_module = MagicMock()
        mock_module.get_weather = mock_get_weather
        mock_import.return_value = mock_module

        reg = ResourceRegistry()
        reg.register_tool("get_weather", ToolConfig(
            type="static", description="Weather", module="src.tools:get_weather"
        ))

        factory = AgentFactory(registry=reg)
        tools = factory._resolve_tools(["get_weather"])

        assert len(tools) == 1
        assert tools[0].__name__ == "get_weather"

    def test_build_instructions_from_template(self):
        reg = ResourceRegistry()
        factory = AgentFactory(registry=reg)
        result = factory._build_instructions(
            agent_config=ResolvedAgentConfig(id="test", name="Test", instructions="Today: {{today}}"),
            skills=[],
        )
        assert "{{today}}" not in result
        assert "Today:" in result
