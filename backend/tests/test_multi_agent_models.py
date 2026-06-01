"""Tests for multi-agent group configuration models."""

import pytest
from src.config.models import (
    AgentConfig,
    MemberConfig,
    WorkflowConfig,
    WorkflowGraph,
    WorkflowGraphEdge,
)


class TestMemberConfig:
    def test_member_config_required_fields(self):
        member = MemberConfig(agent_id="weather_agent")
        assert member.agent_id == "weather_agent"
        assert member.display_name is None

    def test_member_config_full(self):
        member = MemberConfig(
            agent_id="weather_agent",
            display_name="天气专家",
            response_mode="mention_only",
            tools_filter=["get_weather"],
            role_description="查询天气",
        )
        assert member.display_name == "天气专家"
        assert member.tools_filter == ["get_weather"]


class TestWorkflowGraph:
    def test_graph_with_edges(self):
        graph = WorkflowGraph(
            start=["weather_agent"],
            end=["flight_agent"],
            edges=[
                WorkflowGraphEdge(from_="weather_agent", to="hotel_agent"),
                WorkflowGraphEdge(from_="hotel_agent", to="flight_agent"),
            ],
        )
        assert len(graph.edges) == 2
        assert graph.edges[0].from_ == "weather_agent"

    def test_graph_empty_edges_raises(self):
        with pytest.raises(ValueError, match="edges must not be empty"):
            WorkflowGraph(start=["a"], end=["a"], edges=[])


class TestWorkflowConfig:
    def test_workflow_config(self):
        wf = WorkflowConfig(
            id="full_plan",
            description="完整旅行规划",
            graph=WorkflowGraph(
                start=["weather_agent"],
                end=["flight_agent"],
                edges=[
                    WorkflowGraphEdge(from_="weather_agent", to="hotel_agent"),
                ],
            ),
        )
        assert wf.id == "full_plan"
        assert wf.graph.start == ["weather_agent"]


class TestAgentConfigWithKind:
    def test_single_agent_default(self):
        agent = AgentConfig(id="test", name="Test")
        assert agent.kind == "single"
        assert agent.members is None
        assert agent.workflows is None

    def test_multi_agent_with_members(self):
        agent = AgentConfig(
            id="travel_group",
            name="旅行规划群",
            kind="multi",
            members=[
                MemberConfig(agent_id="weather_agent", display_name="天气专家"),
            ],
            workflows=[
                WorkflowConfig(
                    id="full_plan",
                    description="完整规划",
                    graph=WorkflowGraph(
                        start=["weather_agent"],
                        end=["weather_agent"],
                        edges=[WorkflowGraphEdge(from_="weather_agent", to="weather_agent")],
                    ),
                ),
            ],
        )
        assert agent.kind == "multi"
        assert len(agent.members) == 1
        assert len(agent.workflows) == 1
