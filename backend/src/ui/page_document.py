"""Validation and normalization for generated page documents."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from jsonschema import Draft202012Validator, ValidationError

from .component_catalog import ComponentCatalog

VALID_IMPORTANCE = ("primary", "secondary", "supporting")
VALID_GAPS = ("sm", "md", "lg")


class PageDocumentValidationError(ValueError):
    """Raised when a generated page document is unsafe or unsupported."""


def build_page_document_schema(
    catalog: ComponentCatalog,
    *,
    max_items: int = 6,
) -> dict[str, Any]:
    """Build a JSON Schema for generated page documents."""

    component_ids = sorted(catalog.components.keys())

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["version", "layout"],
        "additionalProperties": False,
        "properties": {
            "version": {"const": "1"},
            "title": {"type": "string"},
            "layout": {
                "type": "object",
                "required": ["kind", "columns", "items"],
                "additionalProperties": False,
                "properties": {
                    "kind": {"const": "grid"},
                    "columns": {"const": 12},
                    "gap": {"enum": list(VALID_GAPS)},
                    "items": {
                        "type": "array",
                        "maxItems": max_items,
                        "items": _build_page_item_schema(catalog, component_ids),
                    },
                },
            },
        },
    }


def validate_page_document(
    document: Mapping[str, Any],
    catalog: ComponentCatalog,
    *,
    max_items: int = 6,
) -> dict[str, Any]:
    """Validate and normalize a generated page document."""

    if not isinstance(document, Mapping):
        raise PageDocumentValidationError("PageDocument must be an object")

    prepared_document = _prepare_document_for_validation(document, catalog, max_items=max_items)

    validator = Draft202012Validator(build_page_document_schema(catalog, max_items=max_items))
    error = next(validator.iter_errors(prepared_document), None)
    if error is not None:
        raise PageDocumentValidationError(_format_validation_error(error))

    layout = prepared_document["layout"]
    normalized_items: list[dict[str, Any]] = []
    seen_keys: dict[str, int] = {}
    for raw_item in layout["items"][:max_items]:
        normalized_items.append(_normalize_item(raw_item, catalog, seen_keys))

    normalized_layout: dict[str, Any] = {
        "kind": "grid",
        "columns": 12,
        "items": normalized_items,
    }
    if layout.get("gap") in VALID_GAPS:
        normalized_layout["gap"] = layout["gap"]

    normalized: dict[str, Any] = {
        "version": "1",
        "layout": normalized_layout,
    }
    title = document.get("title")
    if isinstance(title, str) and title.strip():
        normalized["title"] = title.strip()

    return normalized


def _prepare_document_for_validation(
    document: Mapping[str, Any],
    catalog: ComponentCatalog,
    *,
    max_items: int,
) -> dict[str, Any]:
    prepared = deepcopy(dict(document))
    layout = prepared.get("layout")
    if not isinstance(layout, dict):
        return prepared

    raw_items = layout.get("items")
    if not isinstance(raw_items, list):
        return prepared

    trimmed_items = raw_items[:max_items]
    for raw_item in trimmed_items:
        if not isinstance(raw_item, Mapping):
            continue
        component_id = raw_item.get("componentId")
        if isinstance(component_id, str) and component_id not in catalog.components:
            raise PageDocumentValidationError(f"Unknown component: {component_id}")

    layout["items"] = trimmed_items
    return prepared


def _build_page_item_schema(
    catalog: ComponentCatalog,
    component_ids: list[str],
) -> dict[str, Any]:
    item_base = {
        "type": "object",
        "required": ["componentId", "props"],
        "additionalProperties": False,
        "properties": {
            "componentId": {"enum": component_ids},
            "key": {"type": "string", "minLength": 1},
            "span": {"type": "integer"},
            "importance": {"enum": list(VALID_IMPORTANCE)},
            "props": {"type": "object"},
        },
    }

    variants = []
    for component in catalog.components.values():
        variants.append(
            {
                "allOf": [
                    item_base,
                    {
                        "properties": {
                            "componentId": {"const": component.id},
                            "props": _to_jsonable(component.props_schema),
                        }
                    },
                ]
            }
        )

    return {"oneOf": variants}


def _normalize_item(
    raw_item: Mapping[str, Any],
    catalog: ComponentCatalog,
    seen_keys: dict[str, int],
) -> dict[str, Any]:
    component_id = raw_item["componentId"]
    component = catalog.components[component_id]

    raw_key = raw_item.get("key")
    base_key = raw_key.strip() if isinstance(raw_key, str) and raw_key.strip() else component_id
    span = raw_item.get("span")
    if not isinstance(span, int) or isinstance(span, bool) or span not in component.allowed_spans:
        span = component.preferred_span

    item: dict[str, Any] = {
        "componentId": component_id,
        "key": _unique_key(base_key, seen_keys),
        "span": span,
        "props": deepcopy(dict(raw_item["props"])),
    }
    if raw_item.get("importance") in VALID_IMPORTANCE:
        item["importance"] = raw_item["importance"]
    return item


def _unique_key(key: str, seen_keys: dict[str, int]) -> str:
    count = seen_keys.get(key, 0) + 1
    seen_keys[key] = count
    if count == 1:
        return key
    return f"{key}-{count}"


def _format_validation_error(error: ValidationError) -> str:
    path = ".".join(str(part) for part in error.absolute_path)
    if "oneOf" in error.schema_path:
        instance = error.instance
        if isinstance(instance, Mapping):
            component_id = instance.get("componentId")
            if isinstance(component_id, str) and component_id:
                return f"{component_id}.props is invalid"
        return "layout.items item is invalid"
    if path:
        return f"{path}: {error.message}"
    return error.message


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    return value
