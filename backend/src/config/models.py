"""Pydantic models for YAML configuration files."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ModelConfig(BaseModel):
    """LLM model configuration."""

    provider: str
    name: str
    base_url: str | None = None
    api_key_env: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None


class ToolParameter(BaseModel):
    """Tool parameter definition."""

    name: str
    type: str
    required: bool = True


class ToolConfig(BaseModel):
    """Tool registration configuration."""

    type: str = Field(..., pattern="^(static|shared)$")
    description: str
    module: str
    parameters: list[ToolParameter] = Field(default_factory=list)
    approval_mode: str | None = Field(None, pattern="^(never_require|optional|always_require)$")


class MCPServerConfig(BaseModel):
    """MCP server configuration."""

    transport: str = Field(..., pattern="^(sse|stdio)$")
    url: str | None = None
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)


class WorldDefaults(BaseModel):
    """World-level default configuration."""

    model: str | None = None
    skill_directories: list[str] = Field(default_factory=lambda: ["skills"])
    history_persistence: bool = True


class WorldConfig(BaseModel):
    """World registration entry."""

    name: str
    description: str | None = None
    defaults: WorldDefaults = Field(default_factory=WorldDefaults)


class ResolvedAgentConfig(BaseModel):
    """Agent config after merging with world defaults."""

    id: str
    name: str
    description: str | None = None
    model: str | None = None
    instructions: str | None = None
    instructions_template: bool = False
    skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    mcp_tools: list[str] = Field(default_factory=list)
    state_schema: dict[str, Any] | None = None
    history_persistence: bool = True
    framework_name: str | None = None
    framework_description: str | None = None
    predict_state_config: dict[str, Any] | None = None


class AgentConfig(BaseModel):
    """Agent instance configuration."""

    id: str
    name: str
    description: str | None = None
    model: str | None = None
    instructions: str | None = None
    instructions_template: bool = False
    skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    mcp_tools: list[str] = Field(default_factory=list)
    state_schema: dict[str, Any] | None = None
    history_persistence: bool | None = None
    require_per_service_call_history_persistence: bool | None = None
    framework_name: str | None = None
    framework_description: str | None = None
    predict_state_config: dict[str, Any] | None = None

    def merge_with_world_defaults(self, world_defaults: WorldDefaults) -> ResolvedAgentConfig:
        """Merge agent config with world defaults."""
        # Use require_per_service_call_history_persistence as fallback for history_persistence
        effective_history = self.history_persistence
        if effective_history is None:
            effective_history = self.require_per_service_call_history_persistence
        if effective_history is None:
            effective_history = world_defaults.history_persistence

        return ResolvedAgentConfig(
            id=self.id,
            name=self.name,
            description=self.description,
            model=self.model or world_defaults.model,
            instructions=self.instructions,
            instructions_template=self.instructions_template,
            skills=self.skills,
            tools=self.tools,
            mcp_tools=self.mcp_tools,
            state_schema=self.state_schema,
            history_persistence=effective_history,
            framework_name=self.framework_name,
            framework_description=self.framework_description,
            predict_state_config=self.predict_state_config,
        )


class GlobalConfig(BaseModel):
    """Root configuration container."""

    models: dict[str, ModelConfig] = Field(default_factory=dict)
    tools: dict[str, ToolConfig] = Field(default_factory=dict)
    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)
    worlds: dict[str, WorldConfig] = Field(default_factory=dict)


def render_instructions_template(instructions: str) -> str:
    """Replace template variables with actual dates."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)

    return (
        instructions
        .replace("{{today}}", today.isoformat())
        .replace("{{tomorrow}}", tomorrow.isoformat())
        .replace("{{day_after_tomorrow}}", day_after.isoformat())
    )
