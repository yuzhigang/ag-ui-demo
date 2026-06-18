"""Agent factory: builds Agent and AgentFrameworkAgent from YAML config.

The factory is responsible for:
  - Resolving tool names to actual function objects (via registry)
  - Building instruction strings (delegated to builders.instructions)
"""

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING

from src.builders.instructions import (
    build_admin_instructions,
    build_instructions,
    build_member_instructions,
)

if TYPE_CHECKING:
    from .config.models import ResolvedAgentConfig
    from .config.registry import ResourceRegistry

logger = logging.getLogger(__name__)


class AgentFactory:
    """Factory that constructs Agent instances from configuration."""

    def __init__(self, *, registry: ResourceRegistry) -> None:
        self._registry = registry

    def _resolve_tools(self, tool_names: list[str]) -> list:
        """Resolve tool names to actual function objects."""
        tools = []
        for name in tool_names:
            tool_config = self._registry.get_tool(name)
            if tool_config is None:
                raise ValueError(f"Tool '{name}' not found in registry")

            module_path, func_name = tool_config.module.rsplit(":", 1)
            try:
                module = importlib.import_module(module_path)
                func = getattr(module, func_name)
            except (ImportError, AttributeError) as exc:
                if tool_config.type == "static":
                    raise RuntimeError(
                        f"Static tool '{name}' failed to load from '{tool_config.module}'"
                    ) from exc
                logger.warning("Shared tool '%s' failed to load: %s", name, exc)
                continue
            tools.append(func)
        return tools

    def _build_instructions(
        self,
        agent_config: ResolvedAgentConfig,
        skills: list,
    ) -> str:
        """Build instructions from agent config and skills."""
        return build_instructions(agent_config, skills)

    def _build_member_instructions(
        self,
        base_instructions: str,
        member,
    ) -> str:
        """Combine base instructions with member role context."""
        return build_member_instructions(base_instructions, member)

    def _build_admin_instructions(self, config: ResolvedAgentConfig) -> str:
        """Build admin instructions with member list, workflows, and capabilities."""
        return build_admin_instructions(config)
