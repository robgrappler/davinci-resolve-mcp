"""Utilities for defining and wiring MCP handlers."""

from __future__ import annotations

import functools
from dataclasses import dataclass
from typing import Any, Callable, List, Tuple

from mcp.server.fastmcp import FastMCP

from davinci_resolve_mcp.context import ResolveContext


HandlerFunc = Callable[..., Any]
ResourceDef = Tuple[str, HandlerFunc]
ToolDef = HandlerFunc


@dataclass(slots=True)
class HandlerRegistry:
    """Collects handler functions for a module."""

    resources: List[ResourceDef]
    tools: List[ToolDef]

    def __init__(self) -> None:
        self.resources = []
        self.tools = []

    def resource(self, uri: str) -> Callable[[HandlerFunc], HandlerFunc]:
        """Decorator to register a resource handler."""

        def decorator(func: HandlerFunc) -> HandlerFunc:
            self.resources.append((uri, func))
            return func

        return decorator

    def tool(self) -> Callable[[HandlerFunc], HandlerFunc]:
        """Decorator to register a tool handler."""

        def decorator(func: HandlerFunc) -> HandlerFunc:
            self.tools.append(func)
            return func

        return decorator


def install_handlers(
    server: FastMCP,
    context: ResolveContext,
    registry: HandlerRegistry,
    module_globals: dict[str, Any],
) -> None:
    """Register handlers collected in ``registry`` with the MCP server."""

    def wrap(func: HandlerFunc) -> HandlerFunc:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            module_globals["resolve"] = context.resolve()
            return func(*args, **kwargs)

        return wrapper

    for uri, func in registry.resources:
        server.resource(uri)(wrap(func))

    for func in registry.tools:
        server.tool()(wrap(func))
