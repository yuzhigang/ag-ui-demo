"""YAML configuration loader with validation."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from .models import AgentConfig, GlobalConfig, WorldConfig

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and validates YAML configuration files."""

    def __init__(self, *, config_dir: Path | None = None, worlds_dir: Path | None = None) -> None:
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config"
        if worlds_dir is None:
            worlds_dir = Path(__file__).parent.parent.parent / "worlds"

        self.config_dir = Path(config_dir)
        self.worlds_dir = Path(worlds_dir)

        if not self.config_dir.exists():
            raise FileNotFoundError(f"Config directory not found: {self.config_dir}")

    def _load_yaml(self, filename: str) -> dict:
        """Load a single YAML file from config directory."""
        path = self.config_dir / filename
        if not path.exists():
            logger.warning("Config file not found: %s", path)
            return {}
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data

    def load_global_config(self) -> GlobalConfig:
        """Load all global configuration files."""
        models_data = self._load_yaml("models.yaml")
        tools_data = self._load_yaml("tools.yaml")
        mcp_data = self._load_yaml("mcp_servers.yaml")
        worlds_data = self._load_yaml("worlds.yaml")

        return GlobalConfig(
            models=models_data.get("models", {}),
            tools=tools_data.get("tools", {}),
            mcp_servers=mcp_data.get("mcp_servers", {}),
            worlds=worlds_data.get("worlds", {}),
        )

    def load_world_agents(self, world_id: str) -> list[AgentConfig]:
        """Load all agent configs for a given world."""
        world_path = self.worlds_dir / world_id
        if not world_path.exists():
            logger.warning("World directory not found: %s", world_path)
            return []

        agents: list[AgentConfig] = []
        for agent_file in sorted(world_path.glob("*.yaml")):
            with open(agent_file, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            agents.append(AgentConfig(**data))

        return agents

    def load_single_agent(self, world_id: str, agent_id: str) -> AgentConfig | None:
        """Load a single agent config."""
        path = self.worlds_dir / world_id / f"{agent_id}.yaml"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return AgentConfig(**data)
