"""Handlers for Resolve application control helpers."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers
from davinci_resolve_mcp.utils.app_control import (
    quit_resolve_app,
    get_app_state,
    restart_resolve_app,
    open_project_settings,
    open_preferences,
)

logger = logging.getLogger("davinci-resolve-mcp.app_control")
registry = HandlerRegistry()
resource = registry.resource
tool = registry.tool
resolve: Optional[Any] = None


@resource("resolve://app/state")
def get_app_state_endpoint() -> Dict[str, Any]:
    """Get DaVinci Resolve application state information."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "connected": False}

    return get_app_state(resolve)


@tool()
def quit_app(force: bool = False, save_project: bool = True) -> str:
    """
    Quit DaVinci Resolve application.

    Args:
        force: Whether to force quit even if unsaved changes (potentially dangerous)
        save_project: Whether to save the project before quitting
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"

    result = quit_resolve_app(resolve, force, save_project)

    if result:
        return "DaVinci Resolve quit command sent successfully"
    else:
        return "Failed to quit DaVinci Resolve"


@tool()
def restart_app(wait_seconds: int = 5) -> str:
    """
    Restart DaVinci Resolve application.

    Args:
        wait_seconds: Seconds to wait between quit and restart
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"

    result = restart_resolve_app(resolve, wait_seconds)

    if result:
        return "DaVinci Resolve restart initiated successfully"
    else:
        return "Failed to restart DaVinci Resolve"


@tool()
def open_settings() -> str:
    """Open the Project Settings dialog in DaVinci Resolve."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"

    result = open_project_settings(resolve)

    if result:
        return "Project Settings dialog opened successfully"
    else:
        return "Failed to open Project Settings dialog"


@tool()
def open_app_preferences() -> str:
    """Open the Preferences dialog in DaVinci Resolve."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"

    result = open_preferences(resolve)

    if result:
        return "Preferences dialog opened successfully"
    else:
        return "Failed to open Preferences dialog"


def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
