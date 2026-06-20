"""Handlers for workspace layout preset handlers."""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers
from davinci_resolve_mcp.utils.layout_presets import (
    list_layout_presets,
    save_layout_preset,
    load_layout_preset,
    export_layout_preset,
    import_layout_preset,
    delete_layout_preset,
)
from davinci_resolve_mcp.utils.response import success_response, error_response

logger = logging.getLogger("davinci-resolve-mcp.layout_presets")
registry = HandlerRegistry()
resource = registry.resource
tool = registry.tool
resolve: Optional[Any] = None


@resource("resolve://layout-presets")
def get_layout_presets() -> List[Dict[str, Any]]:
    """Get all available layout presets for DaVinci Resolve."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}

    return list_layout_presets(layout_type="ui")


@tool()
def save_layout_preset_tool(preset_name: str) -> Dict[str, Any]:
    """
    Save the current UI layout as a preset.

    Args:
        preset_name: Name for the saved preset
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    result = save_layout_preset(resolve, preset_name, layout_type="ui")
    if result:
        return success_response(
            {"preset_name": preset_name}, message=f"Successfully saved layout preset '{preset_name}'"
        )
    else:
        return error_response(
            "OPERATION_FAILED", f"Failed to save layout preset '{preset_name}'", context={"preset_name": preset_name}
        )


@tool()
def load_layout_preset_tool(preset_name: str) -> Dict[str, Any]:
    """
    Load a UI layout preset.

    Args:
        preset_name: Name of the preset to load
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    result = load_layout_preset(resolve, preset_name, layout_type="ui")
    if result:
        return success_response(
            {"preset_name": preset_name}, message=f"Successfully loaded layout preset '{preset_name}'"
        )
    else:
        return error_response(
            "OPERATION_FAILED", f"Failed to load layout preset '{preset_name}'", context={"preset_name": preset_name}
        )


@tool()
def export_layout_preset_tool(preset_name: str, export_path: str) -> Dict[str, Any]:
    """
    Export a layout preset to a file.

    Args:
        preset_name: Name of the preset to export
        export_path: Path to export the preset file to
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    result = export_layout_preset(preset_name, export_path, layout_type="ui")
    if result:
        return success_response(
            {"preset_name": preset_name, "export_path": export_path},
            message=f"Successfully exported layout preset '{preset_name}' to {export_path}",
        )
    else:
        return error_response(
            "OPERATION_FAILED",
            f"Failed to export layout preset '{preset_name}'",
            context={"preset_name": preset_name, "export_path": export_path},
        )


@tool()
def import_layout_preset_tool(import_path: str, preset_name: str = None) -> Dict[str, Any]:
    """
    Import a layout preset from a file.

    Args:
        import_path: Path to the preset file to import
        preset_name: Name to save the imported preset as (uses filename if None)
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    result = import_layout_preset(import_path, preset_name, layout_type="ui")

    if preset_name is None:
        preset_name = os.path.splitext(os.path.basename(import_path))[0]

    if result:
        return success_response(
            {"preset_name": preset_name, "import_path": import_path},
            message=f"Successfully imported layout preset as '{preset_name}'",
        )
    else:
        return error_response(
            "OPERATION_FAILED",
            f"Failed to import layout preset from {import_path}",
            context={"import_path": import_path, "preset_name": preset_name},
        )


@tool()
def delete_layout_preset_tool(preset_name: str) -> Dict[str, Any]:
    """
    Delete a layout preset.

    Args:
        preset_name: Name of the preset to delete
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    result = delete_layout_preset(preset_name, layout_type="ui")
    if result:
        return success_response(
            {"preset_name": preset_name}, message=f"Successfully deleted layout preset '{preset_name}'"
        )
    else:
        return error_response(
            "OPERATION_FAILED", f"Failed to delete layout preset '{preset_name}'", context={"preset_name": preset_name}
        )


def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
