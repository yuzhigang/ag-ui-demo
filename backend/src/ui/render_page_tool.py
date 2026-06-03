"""Controlled render_page tool for agent-requested generated pages."""

from __future__ import annotations

from typing import Any

from agent_framework import tool


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


@tool(approval_mode="never_require")
def render_page(page: dict) -> dict:
    """请求渲染一个最终生成页面。

    Args:
        page: PageDocument JSON。必须是 version='1'，layout.kind='grid'，columns=12，
            items 最多 6 个。每个 item 必须使用组件目录中的 componentId。
    """

    return render_page_marker(page)
