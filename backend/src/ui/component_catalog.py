"""Load and render UI component catalog metadata."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import yaml
from jsonschema import Draft202012Validator


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(loader: _UniqueKeySafeLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    if not isinstance(node, yaml.MappingNode):
        raise yaml.constructor.ConstructorError(None, None, "expected a mapping node", node.start_mark)

    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"Duplicate key in component catalog YAML: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@dataclass(frozen=True)
class ComponentSpec:
    """Specification for one front-end component available to the runtime."""

    id: str
    description: str
    allowed_spans: tuple[int, ...]
    preferred_span: int
    props_schema: Mapping[str, Any]
    usage_guidance: str
    example_props: Mapping[str, Any]


@dataclass(frozen=True)
class ComponentCatalog:
    """Collection of component specs keyed by component id."""

    components: Mapping[str, ComponentSpec]


def load_component_catalog(path: Path) -> ComponentCatalog:
    """Load component metadata from a YAML catalog file."""

    with open(path, encoding="utf-8") as f:
        try:
            data = yaml.load(f, Loader=_UniqueKeySafeLoader)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid component catalog YAML: {exc}") from exc

    if not isinstance(data, Mapping):
        raise ValueError(f"Component catalog must be a mapping: {path}")

    raw_components = data.get("components")
    if not isinstance(raw_components, Mapping):
        raise ValueError("Component catalog field 'components' must be a mapping")

    components: dict[str, ComponentSpec] = {}
    for entry_name, component_data in raw_components.items():
        if not isinstance(component_data, Mapping):
            raise ValueError(f"Component entry '{entry_name}' must be a mapping")

        component = _build_component_spec(entry_name, component_data)
        if component.id in components:
            raise ValueError(f"Duplicate component id: {component.id}")
        components[component.id] = component

    return ComponentCatalog(components=MappingProxyType(components))


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


def _build_component_spec(entry_name: Any, component_data: Mapping[str, Any]) -> ComponentSpec:
    component_id = component_data.get("id")
    if not isinstance(component_id, str) or not component_id.strip():
        raise ValueError(f"Component entry '{entry_name}' must define a non-empty string id")

    description = _required_string(component_data, "description", component_id)
    usage_guidance = _required_string(component_data, "usage_guidance", component_id)
    allowed_spans = _validate_allowed_spans(component_data.get("allowed_spans"), component_id)
    preferred_span = component_data.get("preferred_span")
    if not isinstance(preferred_span, int) or isinstance(preferred_span, bool):
        raise ValueError(f"Component '{component_id}' preferred_span must be an int")
    if preferred_span not in allowed_spans:
        raise ValueError(f"Component '{component_id}' preferred_span must be in allowed_spans")

    props_schema = component_data.get("props_schema")
    if not isinstance(props_schema, Mapping):
        raise ValueError(f"Component '{component_id}' props_schema must be a mapping")
    _validate_props_schema(props_schema, component_id)

    example_props = component_data.get("example_props")
    if not isinstance(example_props, Mapping):
        raise ValueError(f"Component '{component_id}' example_props must be a mapping")

    return ComponentSpec(
        id=component_id,
        description=description,
        allowed_spans=allowed_spans,
        preferred_span=preferred_span,
        props_schema=_freeze_mapping(props_schema),
        usage_guidance=usage_guidance,
        example_props=_freeze_mapping(example_props),
    )


def _required_string(component_data: Mapping[str, Any], field: str, component_id: str) -> str:
    value = component_data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Component '{component_id}' {field} must be a non-empty string")
    return value


def _validate_allowed_spans(value: Any, component_id: str) -> tuple[int, ...]:
    if not isinstance(value, (list, tuple)) or not value:
        raise ValueError(f"Component '{component_id}' allowed_spans must be a non-empty list of ints")
    if not all(isinstance(span, int) and not isinstance(span, bool) for span in value):
        raise ValueError(f"Component '{component_id}' allowed_spans must contain only ints")
    return tuple(value)


def _validate_props_schema(props_schema: Mapping[Any, Any], component_id: str) -> None:
    try:
        Draft202012Validator.check_schema(_to_jsonable(props_schema))
    except Exception as exc:
        raise ValueError(f"Component '{component_id}' props_schema must be valid JSON Schema") from exc

    schema_type = props_schema.get("type")
    if schema_type != "object":
        raise ValueError(f"Component '{component_id}' props_schema type must be 'object'")

    properties = props_schema.get("properties")
    if not isinstance(properties, Mapping) or not properties:
        raise ValueError(f"Component '{component_id}' props_schema.properties must be a non-empty mapping")


def _list_declared_props(props_schema: Mapping[str, Any]) -> tuple[str, ...]:
    properties = props_schema.get("properties")
    if not isinstance(properties, Mapping):
        return ()
    return tuple(key for key in properties.keys() if isinstance(key, str))


def _freeze_mapping(value: Mapping[Any, Any]) -> Mapping[Any, Any]:
    frozen = {key: _deep_freeze(deepcopy(item)) for key, item in value.items()}
    return MappingProxyType(frozen)


def _deep_freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    return value
