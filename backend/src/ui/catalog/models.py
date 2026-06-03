"""Component catalog data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ComponentSpec:
    """Specification for one front-end component available to the runtime."""

    id: str
    description: str
    allowed_spans: tuple[int, ...]
    preferred_span: int
    props_schema: Mapping[str, Any]
    usage_guidance: str
    example_props: Mapping[str, Any]


@dataclass(frozen=True)
class ComponentCatalog:
    """Collection of component specs keyed by component id."""

    components: Mapping[str, ComponentSpec]
