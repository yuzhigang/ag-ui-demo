"""JSON Schema builders for generated page documents."""

from __future__ import annotations

from typing import Any, Mapping

from ..catalog import ComponentCatalog

VALID_IMPORTANCE = ("primary", "secondary", "supporting")
VALID_GAPS = ("sm", "md", "lg")


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


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    return value
