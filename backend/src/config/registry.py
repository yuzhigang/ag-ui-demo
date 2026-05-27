"""Runtime resource registry for models, tools, and MCP servers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import MCPServerConfig, ModelConfig, ToolConfig

logger = logging.getLogger(__name__)


class ResourceRegistry:
    """Holds registered resources (models, tools, mcp_servers) in memory."""

    def __init__(self) -> None:
        self._models: dict[str, ModelConfig] = {}
        self._tools: dict[str, ToolConfig] = {}
        self._mcp_servers: dict[str, MCPServerConfig] = {}

    def clear(self) -> None:
        """Clear all registered resources."""
        self._models.clear()
        self._tools.clear()
        self._mcp_servers.clear()

    # Models
    def register_model(self, key: str, config: ModelConfig) -> None:
        self._models[key] = config

    def get_model(self, key: str) -> ModelConfig | None:
        return self._models.get(key)

    def list_models(self) -> list[str]:
        return list(self._models.keys())

    # Tools
    def register_tool(self, key: str, config: ToolConfig) -> None:
        self._tools[key] = config

    def get_tool(self, key: str) -> ToolConfig | None:
        return self._tools.get(key)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def list_static_tools(self) -> list[str]:
        return [k for k, v in self._tools.items() if v.type == "static"]

    def list_shared_tools(self) -> list[str]:
        return [k for k, v in self._tools.items() if v.type == "shared"]

    # MCP Servers
    def register_mcp_server(self, key: str, config: MCPServerConfig) -> None:
        self._mcp_servers[key] = config

    def get_mcp_server(self, key: str) -> MCPServerConfig | None:
        return self._mcp_servers.get(key)

    def list_mcp_servers(self) -> list[str]:
        return list(self._mcp_servers.keys())
