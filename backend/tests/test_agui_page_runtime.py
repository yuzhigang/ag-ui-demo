import json

import pytest
from ag_ui.core import CustomEvent, ToolCallResultEvent, ToolCallStartEvent
from agent_framework.ag_ui import AgentFrameworkAgent

from src.ui.catalog import ComponentCatalog, ComponentSpec
from src.ui.runtime import AGUIPageRuntime
from src.ui.tools import render_page_marker


@pytest.fixture
def anyio_backend():
    return "asyncio"


class FakeRunner:
    async def run(self, input_data):
        yield ToolCallStartEvent(toolCallId="call_1", toolCallName="render_page")
        yield ToolCallResultEvent(
            messageId="msg_1",
            toolCallId="call_1",
            content=json.dumps(
                render_page_marker(
                    {
                        "version": "1",
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
                ),
                ensure_ascii=False,
            ),
        )


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
            )
        }
    )


@pytest.mark.anyio
async def test_runtime_injects_render_page_custom_event():
    runtime = AGUIPageRuntime(FakeRunner(), catalog=_catalog())

    events = [event async for event in runtime.run({"messages": []})]

    custom_events = [event for event in events if isinstance(event, CustomEvent)]
    assert len(custom_events) == 1
    assert custom_events[0].name == "render_page"
    assert custom_events[0].value["layout"]["items"][0]["componentId"] == "WeatherCard"


@pytest.mark.anyio
async def test_runtime_keeps_original_tool_events():
    runtime = AGUIPageRuntime(FakeRunner(), catalog=_catalog())

    events = [event async for event in runtime.run({"messages": []})]

    assert isinstance(events[0], ToolCallStartEvent)
    assert isinstance(events[1], ToolCallResultEvent)


def test_runtime_is_accepted_as_agui_protocol_runner():
    runtime = AGUIPageRuntime(FakeRunner(), catalog=_catalog())

    assert isinstance(runtime, AgentFrameworkAgent)
