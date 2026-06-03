from src.ui.catalog import ComponentCatalog, ComponentSpec
from src.ui.tools.render_page import build_render_page_parameters_schema


def test_render_page_parameters_schema_wraps_page_document_schema():
    catalog = ComponentCatalog(
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
            )
        }
    )

    schema = build_render_page_parameters_schema(catalog)

    assert schema["type"] == "object"
    assert schema["required"] == ["page"]
    page_schema = schema["properties"]["page"]
    assert page_schema["properties"]["version"] == {"const": "1"}
    item_schema = page_schema["properties"]["layout"]["properties"]["items"]["items"]
    assert item_schema["oneOf"][0]["allOf"][1]["properties"]["componentId"] == {"const": "WeatherCard"}
