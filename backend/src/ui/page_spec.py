"""Validation for generated grid PageSpec payloads."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .component_catalog import ComponentCatalog


class PageSpecValidationError(ValueError):
    """Raised when a generated PageSpec is unsafe or unsupported."""


def validate_page_spec(
    page: Mapping[str, Any],
    catalog: ComponentCatalog,
    *,
    max_items: int = 6,
) -> dict[str, Any]:
    """Validate and normalize a generated frontend PageSpec."""

    if not isinstance(page, Mapping):
        raise PageSpecValidationError("PageSpec must be an object")
    if page.get("version") != "1":
        raise PageSpecValidationError("Unsupported PageSpec version")

    layout = page.get("layout")
    if not isinstance(layout, Mapping):
        raise PageSpecValidationError("PageSpec.layout must be an object")
    if layout.get("kind") != "grid":
        raise PageSpecValidationError("Only grid layout is supported")
    if layout.get("columns") != 12:
        raise PageSpecValidationError("Only 12-column grid layout is supported")

    raw_items = layout.get("items")
    if not isinstance(raw_items, list):
        raise PageSpecValidationError("PageSpec.layout.items must be an array")

    normalized_items: list[dict[str, Any]] = []
    seen_keys: dict[str, int] = {}
    for raw_item in raw_items[:max_items]:
        normalized_items.append(_normalize_item(raw_item, catalog, seen_keys))

    normalized_layout: dict[str, Any] = {
        "kind": "grid",
        "columns": 12,
        "items": normalized_items,
    }
    if layout.get("gap") in {"sm", "md", "lg"}:
        normalized_layout["gap"] = layout["gap"]

    normalized: dict[str, Any] = {
        "version": "1",
        "layout": normalized_layout,
    }
    title = page.get("title")
    if isinstance(title, str) and title.strip():
        normalized["title"] = title.strip()

    return normalized


def _normalize_item(
    raw_item: Any,
    catalog: ComponentCatalog,
    seen_keys: dict[str, int],
) -> dict[str, Any]:
    if not isinstance(raw_item, Mapping):
        raise PageSpecValidationError("Grid item must be an object")

    component_id = raw_item.get("componentId")
    if not isinstance(component_id, str) or not component_id.strip():
        raise PageSpecValidationError("Grid item componentId must be a non-empty string")
    component = catalog.components.get(component_id)
    if component is None:
        raise PageSpecValidationError(f"Unknown component: {component_id}")

    props = raw_item.get("props")
    if not isinstance(props, Mapping):
        raise PageSpecValidationError(f"{component_id}.props must be an object")
    _validate_props(component_id, props, component.props_schema)

    raw_key = raw_item.get("key")
    base_key = raw_key.strip() if isinstance(raw_key, str) and raw_key.strip() else component_id
    span = raw_item.get("span")
    if not isinstance(span, int) or isinstance(span, bool) or span not in component.allowed_spans:
        span = component.preferred_span

    item: dict[str, Any] = {
        "componentId": component_id,
        "key": _unique_key(base_key, seen_keys),
        "span": span,
        "props": deepcopy(dict(props)),
    }
    if raw_item.get("importance") in {"primary", "secondary", "supporting"}:
        item["importance"] = raw_item["importance"]
    return item


def _unique_key(key: str, seen_keys: dict[str, int]) -> str:
    count = seen_keys.get(key, 0) + 1
    seen_keys[key] = count
    if count == 1:
        return key
    return f"{key}-{count}"


def _validate_props(component_id: str, props: Mapping[str, Any], schema: Mapping[str, str]) -> None:
    for name, kind in schema.items():
        if name not in props:
            raise PageSpecValidationError(f"{component_id}.props.{name} is required")

        value = props[name]
        if kind == "string" and not isinstance(value, str):
            raise PageSpecValidationError(f"{component_id}.props.{name} must be string")
        if kind == "number" and (
            not isinstance(value, int | float) or isinstance(value, bool)
        ):
            raise PageSpecValidationError(f"{component_id}.props.{name} must be number")
        if kind == "array" and not isinstance(value, list):
            raise PageSpecValidationError(f"{component_id}.props.{name} must be array")
        if kind == "object" and not isinstance(value, Mapping):
            raise PageSpecValidationError(f"{component_id}.props.{name} must be object")
