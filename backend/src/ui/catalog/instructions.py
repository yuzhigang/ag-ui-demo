"""Render component catalog metadata for model instructions."""

from __future__ import annotations

import json
from typing import Any, Mapping

from .models import ComponentCatalog


def render_catalog_for_instructions(catalog: ComponentCatalog) -> str:
    """Render a compact catalog summary for model instructions."""

    lines = [
        "可用前端组件:",
        "根据请求选择组件并输出组件 id、span 和 props；不要输出 HTML、CSS、JSX。",
    ]
    for component in catalog.components.values():
        allowed_spans = ",".join(str(span) for span in component.allowed_spans)
        props = ",".join(_list_declared_props(component.props_schema))
        example_props = json.dumps(_to_jsonable(component.example_props), ensure_ascii=False, sort_keys=True)
        lines.append(
            f"- {component.id}: {component.description} "
            f"allowedSpans={allowed_spans}; preferredSpan={component.preferred_span}; "
            f"props={props}; guidance={component.usage_guidance}; "
            f"exampleProps={example_props}"
        )

    return "\n".join(lines)


def _list_declared_props(props_schema: Mapping[str, Any]) -> tuple[str, ...]:
    properties = props_schema.get("properties")
    if not isinstance(properties, Mapping):
        return ()
    return tuple(key for key in properties.keys() if isinstance(key, str))


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    return value
