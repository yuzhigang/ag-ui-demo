"""Controlled render_page tool for agent-requested generated pages."""

from __future__ import annotations

from typing import Any

from agent_framework import tool

from ..catalog import ComponentCatalog
from ..page_document import build_page_document_schema


RENDER_PAGE_MARKER = "__agui_render_page__"


def render_page_marker(page: dict[str, Any]) -> dict[str, Any]:
    """Wrap a page document so the AG-UI runtime can recognize it safely."""

    return {
        RENDER_PAGE_MARKER: True,
        "page": page,
    }


def extract_render_page_marker(value: Any) -> dict[str, Any] | None:
    """Return the page document from a render_page marker payload if present."""

    if isinstance(value, dict) and value.get(RENDER_PAGE_MARKER) is True:
        page = value.get("page")
        return page if isinstance(page, dict) else None
    return None


def build_render_page_parameters_schema(
    catalog: ComponentCatalog,
    *,
    max_items: int = 6,
) -> dict[str, Any]:
    """Build the JSON Schema for render_page tool arguments."""

    return {
        "type": "object",
        "required": ["page"],
        "additionalProperties": False,
        "properties": {
            "page": build_page_document_schema(catalog, max_items=max_items),
        },
    }


@tool(approval_mode="never_require")
def render_page(page: dict) -> dict:
    """请求渲染一个最终生成页面。

    Args:
        page: PageDocument JSON。必须是 version='1'，layout.kind='grid'，columns=12，
            items 最多 6 个。每个 item 必须使用组件目录中的 componentId。
    """

    return render_page_marker(page)
