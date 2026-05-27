"""Tests for configuration loader."""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.config.loader import ConfigLoader
from src.config.models import GlobalConfig


class TestConfigLoader:
    def test_load_models_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "models.yaml").write_text("""
models:
  deepseek-flash:
    provider: deepseek
    name: deepseek-v4-flash
    base_url: https://api.deepseek.com
    api_key_env: DEEPSEEK_API_KEY
""")
            loader = ConfigLoader(config_dir=config_dir)
            config = loader.load_global_config()

            assert "deepseek-flash" in config.models
            assert config.models["deepseek-flash"].provider == "deepseek"

    def test_load_tools_yaml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            (config_dir / "tools.yaml").write_text("""
tools:
  get_weather:
    type: static
    description: Query weather
    module: src.tools:get_weather
""")
            loader = ConfigLoader(config_dir=config_dir)
            config = loader.load_global_config()

            assert "get_weather" in config.tools
            assert config.tools["get_weather"].type == "static"

    def test_missing_config_dir(self):
        with pytest.raises(FileNotFoundError):
            ConfigLoader(config_dir=Path("/nonexistent"))
