import pytest

from src.ui.catalog import ComponentCatalog, ComponentSpec
from src.ui.page_document import PageDocumentValidationError, validate_page_document


def _catalog() -> ComponentCatalog:
    return ComponentCatalog(
        components={
            "WeatherCard": ComponentSpec(
                id="WeatherCard",
                description="Weather",
                allowed_spans=(3, 4, 6),
                preferred_span=4,
                props_schema={
                    "type": "object",
                    "required": ["city", "temperature"],
                    "additionalProperties": False,
                    "properties": {
                        "city": {"type": "string"},
                        "temperature": {"type": "string"},
                    },
                },
                usage_guidance="Use for weather.",
                example_props={},
            ),
            "HotelList": ComponentSpec(
                id="HotelList",
                description="Hotels",
                allowed_spans=(6, 8, 12),
                preferred_span=8,
                props_schema={
                    "type": "object",
                    "required": ["hotels"],
                    "additionalProperties": False,
                    "properties": {
                        "hotels": {"type": "array"},
                    },
                },
                usage_guidance="Use for hotels.",
                example_props={},
            ),
        }
    )


def test_validate_page_document_accepts_valid_page():
    page = {
        "version": "1",
        "title": "Trip",
        "layout": {
            "kind": "grid",
            "columns": 12,
            "items": [
                {
                    "componentId": "WeatherCard",
                    "key": "weather",
                    "span": 4,
                    "props": {"city": "北京", "temperature": "28°C"},
                }
            ],
        },
    }

    normalized = validate_page_document(page, _catalog())

    assert normalized["title"] == "Trip"
    assert normalized["layout"]["items"][0]["span"] == 4


def test_validate_page_document_normalizes_invalid_span():
    page = {
        "version": "1",
        "layout": {
            "kind": "grid",
            "columns": 12,
            "items": [
                {
                    "componentId": "WeatherCard",
                    "key": "weather",
                    "span": 8,
                    "props": {"city": "北京", "temperature": "28°C"},
                }
            ],
        },
    }

    normalized = validate_page_document(page, _catalog())

    assert normalized["layout"]["items"][0]["span"] == 4


def test_validate_page_document_rejects_unknown_component():
    page = {
        "version": "1",
        "layout": {
            "kind": "grid",
            "columns": 12,
            "items": [
                {
                    "componentId": "UnknownCard",
                    "key": "unknown",
                    "span": 12,
                    "props": {},
                }
            ],
        },
    }

    with pytest.raises(PageDocumentValidationError, match="Unknown component"):
        validate_page_document(page, _catalog())


def test_validate_page_document_rejects_invalid_props():
    page = {
        "version": "1",
        "layout": {
            "kind": "grid",
            "columns": 12,
            "items": [
                {
                    "componentId": "HotelList",
                    "key": "hotels",
                    "span": 8,
                    "props": {"hotels": "not-an-array"},
                }
            ],
        },
    }

    with pytest.raises(PageDocumentValidationError, match="HotelList.props is invalid"):
        validate_page_document(page, _catalog())


def test_validate_page_document_makes_duplicate_keys_unique_and_limits_items():
    items = [
        {
            "componentId": "WeatherCard",
            "key": "same",
            "span": 4,
            "props": {"city": f"城市{idx}", "temperature": "28°C"},
            "importance": "supporting",
        }
        for idx in range(8)
    ]
    page = {"version": "1", "layout": {"kind": "grid", "columns": 12, "items": items}}

    normalized = validate_page_document(page, _catalog(), max_items=6)

    keys = [item["key"] for item in normalized["layout"]["items"]]
    assert len(keys) == 6
    assert len(set(keys)) == 6
    assert keys[0] == "same"
    assert keys[1] == "same-2"
