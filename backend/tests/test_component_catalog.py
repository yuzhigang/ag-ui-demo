"""Tests for UI component catalog loading and prompt rendering."""

from pathlib import Path

import pytest

from src.ui.component_catalog import load_component_catalog, render_catalog_for_instructions


def test_load_component_catalog_reads_weather_card():
    catalog = load_component_catalog(Path("config/components.yaml"))

    weather_card = catalog.components["WeatherCard"]

    assert weather_card.id == "WeatherCard"
    assert weather_card.allowed_spans == (3, 4, 6)
    assert weather_card.preferred_span == 4
    assert weather_card.props_schema["city"] == "string"


def test_loaded_catalog_is_immutable_enough_for_runtime_use():
    catalog = load_component_catalog(Path("config/components.yaml"))
    weather_card = catalog.components["WeatherCard"]

    with pytest.raises(TypeError):
        catalog.components["OtherCard"] = weather_card

    with pytest.raises(AttributeError):
        weather_card.allowed_spans.append(12)

    with pytest.raises(TypeError):
        weather_card.props_schema["city"] = "number"

    with pytest.raises(TypeError):
        weather_card.example_props["city"] = "Beijing"

    assert "OtherCard" not in catalog.components
    assert weather_card.allowed_spans == (3, 4, 6)
    assert weather_card.props_schema["city"] == "string"
    assert weather_card.example_props["city"] == "Shanghai"


def test_render_catalog_for_instructions_summarizes_available_components():
    catalog = load_component_catalog(Path("config/components.yaml"))

    instructions = render_catalog_for_instructions(catalog)

    assert "可用前端组件" in instructions
    assert "WeatherCard" in instructions
    assert "allowedSpans=3,4,6" in instructions
    assert "不要输出 HTML、CSS、JSX" in instructions
    assert "'city': 'Shanghai'" not in instructions


def test_duplicate_component_ids_raise_value_error(tmp_path):
    catalog_path = tmp_path / "components.yaml"
    catalog_path.write_text(
        """
components:
  WeatherCard:
    id: WeatherCard
    description: Weather
    allowed_spans: [3]
    preferred_span: 3
    props_schema:
      city: string
    usage_guidance: Use for weather.
    example_props:
      city: Shanghai
  WeatherCardAlias:
    id: WeatherCard
    description: Duplicate weather
    allowed_spans: [4]
    preferred_span: 4
    props_schema:
      city: string
    usage_guidance: Use for duplicate weather.
    example_props:
      city: Beijing
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate component id"):
        load_component_catalog(catalog_path)


def test_invalid_preferred_span_raises_value_error(tmp_path):
    catalog_path = tmp_path / "components.yaml"
    catalog_path.write_text(
        """
components:
  WeatherCard:
    id: WeatherCard
    description: Weather
    allowed_spans: [3, 4, 6]
    preferred_span: 8
    props_schema:
      city: string
    usage_guidance: Use for weather.
    example_props:
      city: Shanghai
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="preferred_span"):
        load_component_catalog(catalog_path)


def test_invalid_props_schema_kind_raises_value_error(tmp_path):
    catalog_path = tmp_path / "components.yaml"
    catalog_path.write_text(
        """
components:
  WeatherCard:
    id: WeatherCard
    description: Weather
    allowed_spans: [3]
    preferred_span: 3
    props_schema:
      city: boolean
    usage_guidance: Use for weather.
    example_props:
      city: Shanghai
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="props_schema"):
        load_component_catalog(catalog_path)
