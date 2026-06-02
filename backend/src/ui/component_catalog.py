"""Load and render UI component catalog metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ComponentSpec:
    """Specification for one front-end component available to the runtime."""

    id: str
    description: str
    allowed_spans: list[int]
    preferred_span: int
    props_schema: dict[str, Any]
    usage_guidance: str
    example_props: dict[str, Any]


@dataclass(frozen=True)
class ComponentCatalog:
    """Collection of component specs keyed by component id."""

    components: dict[str, ComponentSpec]


def load_component_catalog(path: Path) -> ComponentCatalog:
    """Load component metadata from a YAML catalog file."""

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    components = {}
    for component_data in data.get("components", []):
        component = ComponentSpec(**component_data)
        components[component.id] = component

    return ComponentCatalog(components=components)


def render_catalog_for_instructions(catalog: ComponentCatalog) -> str:
    """Render a compact catalog summary for model instructions."""

    lines = [
        "可用前端组件:",
        "根据请求选择组件并输出组件 id、span 和 props；不要输出 HTML、CSS、JSX。",
    ]
    for component in catalog.components.values():
        allowed_spans = ",".join(str(span) for span in component.allowed_spans)
        props = ",".join(component.props_schema.keys())
        lines.append(
            f"- {component.id}: {component.description} "
            f"allowedSpans={allowed_spans}; preferredSpan={component.preferred_span}; "
            f"props={props}; guidance={component.usage_guidance}; "
            f"exampleProps={component.example_props}"
        )

    return "\n".join(lines)
