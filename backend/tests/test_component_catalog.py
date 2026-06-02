"""Tests for UI component catalog loading and prompt rendering."""

from pathlib import Path

from src.ui.component_catalog import load_component_catalog, render_catalog_for_instructions


def test_load_component_catalog_reads_weather_card():
    catalog = load_component_catalog(Path("config/components.yaml"))

    weather_card = catalog.components["WeatherCard"]

    assert weather_card.id == "WeatherCard"
    assert weather_card.allowed_spans == [3, 4, 6]
    assert weather_card.preferred_span == 4
    assert weather_card.props_schema["city"] == "string"


def test_render_catalog_for_instructions_summarizes_available_components():
    catalog = load_component_catalog(Path("config/components.yaml"))

    instructions = render_catalog_for_instructions(catalog)

    assert "可用前端组件" in instructions
    assert "WeatherCard" in instructions
    assert "allowedSpans=3,4,6" in instructions
    assert "不要输出 HTML、CSS、JSX" in instructions
