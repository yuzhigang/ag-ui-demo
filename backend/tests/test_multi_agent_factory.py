"""Tests for multi-agent group factory."""

from unittest.mock import MagicMock, patch

from src.config.models import (
    AgentConfig,
    MemberConfig,
    ModelConfig,
    ResolvedAgentConfig,
    ToolConfig,
    WorkflowConfig,
    WorkflowGraph,
    WorkflowGraphEdge,
)
from src.config.registry import ResourceRegistry
from src.factory import AgentFactory


class TestMultiAgentFactory:
    def test_build_member_instructions(self):
        """Test that member instructions include role_description and suffix."""
        reg = ResourceRegistry()
        factory = AgentFactory(registry=reg)

        member = MemberConfig(
            agent_id="weather_agent",
            display_name="天气专家",
            role_description="查询目的地天气",
            instructions_suffix="你只回答天气问题。",
        )

        result = factory._build_member_instructions(
            base_instructions="你是天气助手。",
            member=member,
        )

        assert "你是天气助手。" in result
        assert "查询目的地天气" in result
        assert "你只回答天气问题。" in result

    def test_build_admin_instructions_with_workflows(self):
        """Test that admin instructions include workflow list and capabilities."""
        reg = ResourceRegistry()
        factory = AgentFactory(registry=reg)

        config = ResolvedAgentConfig(
            id="travel_group",
            name="旅行规划群",
            kind="multi",
            members=[
                MemberConfig(agent_id="w", display_name="天气"),
            ],
            workflows=[
                WorkflowConfig(
                    id="full_plan",
                    description="完整规划",
                    graph=WorkflowGraph(
                        start=["w"],
                        end=["w"],
                        edges=[WorkflowGraphEdge(from_="w", to="w")],
                    ),
                ),
            ],
            capabilities="天气查询、酒店搜索",
        )

        result = factory._build_admin_instructions(config)

        assert "旅行规划群" in result
        assert "天气查询、酒店搜索" in result
        assert "full_plan" in result
        assert "完整规划" in result
