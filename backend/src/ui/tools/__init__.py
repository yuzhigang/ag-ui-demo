"""UI tools callable by agents."""

from .render_page import (
    build_render_page_parameters_schema,
    extract_render_page_marker,
    render_page,
    render_page_marker,
)

__all__ = [
    "build_render_page_parameters_schema",
    "extract_render_page_marker",
    "render_page",
    "render_page_marker",
]
