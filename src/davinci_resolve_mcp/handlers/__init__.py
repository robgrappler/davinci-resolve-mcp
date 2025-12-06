"""Handler registration utilities."""

from __future__ import annotations

from typing import Iterable

from mcp.server.fastmcp import FastMCP

from davinci_resolve_mcp.context import ResolveContext

from . import (
    app_control,
    cache,
    cloud,
    color,
    color_presets,
    delivery,
    inspection,
    keyframes,
    layout_presets,
    media_pool,
    project_properties,
    projects,
    system,
    timeline_items,
    timelines,
)


MODULES = (
    system,
    projects,
    timelines,
    media_pool,
    color,
    delivery,
    cache,
    timeline_items,
    keyframes,
    color_presets,
    inspection,
    layout_presets,
    app_control,
    cloud,
    project_properties,
)


def register_all(server: FastMCP, context: ResolveContext) -> None:
    """Register every handler module with the MCP server."""
    for module in MODULES:
        module.register(server, context)
