"""Handlers for core Resolve metadata and workspace navigation handlers."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers
from davinci_resolve_mcp.utils.response import error_response, success_response

logger = logging.getLogger("davinci-resolve-mcp.system")
registry = HandlerRegistry()
resource = registry.resource
tool = registry.tool
resolve: Optional[Any] = None


@resource("resolve://version")
def get_resolve_version() -> str:
    """Get DaVinci Resolve version information."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    return f"{resolve.GetProductName()} {resolve.GetVersionString()}"


@resource("resolve://current-page")
def get_current_page() -> str:
    """Get the current page open in DaVinci Resolve (Edit, Color, Fusion, etc.)."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    return resolve.GetCurrentPage()


@tool()
def switch_page(page: str) -> Dict[str, Any]:
    """Switch to a specific page in DaVinci Resolve.

    Args:
        page: The page to switch to. Options: 'media', 'cut', 'edit', 'fusion', 'color', 'fairlight', 'deliver'
    """
    if resolve is None:
        return error_response("NOT_CONNECTED", "Not connected to DaVinci Resolve")

    valid_pages = ["media", "cut", "edit", "fusion", "color", "fairlight", "deliver"]
    page = page.lower()

    if page not in valid_pages:
        return error_response(
            "INVALID_ARG",
            f"Invalid page name. Must be one of: {', '.join(valid_pages)}",
            context={"valid_pages": valid_pages},
        )

    result = resolve.OpenPage(page)
    if result:
        return success_response(message=f"Switched to {page} page", context={"page": page})
    else:
        return error_response("OPERATION_FAILED", f"Failed to switch to {page} page", context={"page": page})


@tool()
def debug_environment() -> Dict[str, Any]:
    """Get debug information about the server environment."""
    import sys
    import os
    import platform

    payload = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "sys_path": sys.path,
        "os_environ": {k: v for k, v in os.environ.items() if "RESOLVE" in k or "PYTHON" in k},
        "cwd": os.getcwd(),
        "resolve_connected": resolve is not None,
        "resolve_product": resolve.GetProductName() if resolve else None,
        "resolve_version": resolve.GetVersionString() if resolve else None,
    }
    return success_response(data=payload, message="Debug environment info")


def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
