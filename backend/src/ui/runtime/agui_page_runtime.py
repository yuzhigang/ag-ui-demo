"""AG-UI runtime wrapper that injects validated render_page CustomEvents."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

from ag_ui.core import CustomEvent, ToolCallResultEvent
from agent_framework.ag_ui import AgentFrameworkAgent

from ..catalog import ComponentCatalog
from ..page_document import PageDocumentValidationError, validate_page_document
from ..tools.render_page import extract_render_page_marker


class AGUIPageRuntime(AgentFrameworkAgent):
    """Proxy an AG-UI runner and emit render_page events from tool results."""

    def __init__(self, runner: Any, *, catalog: ComponentCatalog) -> None:
        self._runner = runner
        self._catalog = catalog

    def __getattr__(self, name: str) -> Any:
        return getattr(self._runner, name)

    async def run(self, input_data: dict[str, Any]) -> AsyncGenerator[Any]:
        async for event in self._runner.run(input_data):
            yield event
            custom_event = self._custom_event_from_tool_result(event)
            if custom_event is not None:
                yield custom_event

    def _custom_event_from_tool_result(self, event: Any) -> CustomEvent | None:
        if not isinstance(event, ToolCallResultEvent):
            return None

        content = _decode_tool_result_content(event.content)
        page = extract_render_page_marker(content)
        if page is None:
            return None

        try:
            normalized = validate_page_document(page, self._catalog)
        except PageDocumentValidationError:
            return None

        return CustomEvent(name="render_page", value=normalized)


def _decode_tool_result_content(content: Any) -> Any:
    if not isinstance(content, str):
        return content
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None
