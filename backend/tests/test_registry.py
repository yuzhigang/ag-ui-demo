"""Tests for resource registry."""

from src.config.models import ModelConfig, ToolConfig
from src.config.registry import ResourceRegistry


class TestResourceRegistry:
    def test_register_and_get_model(self):
        reg = ResourceRegistry()
        reg.register_model("flash", ModelConfig(provider="deepseek", name="flash"))
        assert reg.get_model("flash").name == "flash"

    def test_get_missing_model(self):
        reg = ResourceRegistry()
        assert reg.get_model("missing") is None

    def test_register_tool(self):
        reg = ResourceRegistry()
        reg.register_tool("get_weather", ToolConfig(
            type="static", description="Weather", module="src.tools:get_weather"
        ))
        assert "get_weather" in reg.list_tools()
