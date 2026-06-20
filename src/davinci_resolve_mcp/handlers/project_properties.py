"""Handlers for project settings/property helpers."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers
from davinci_resolve_mcp.utils.project_properties import (
    get_all_project_properties,
    get_project_property,
    set_project_property,
    get_timeline_format_settings,
    set_timeline_format,
    get_superscale_settings,
    set_superscale_settings,
    get_color_settings,
    set_color_science_mode,
    set_color_space,
    get_project_metadata,
    get_project_info,
)
from davinci_resolve_mcp.utils.response import success_response, error_response

logger = logging.getLogger("davinci-resolve-mcp.project_properties")
registry = HandlerRegistry()
resource = registry.resource
tool = registry.tool
resolve: Optional[Any] = None


@resource("resolve://project/properties")
def get_project_properties_endpoint() -> Dict[str, Any]:
    """Get all project properties for the current project."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}

    return get_all_project_properties(current_project)


@resource("resolve://project/property/{property_name}")
def get_project_property_endpoint(property_name: str) -> Dict[str, Any]:
    """Get a specific project property value.

    Args:
        property_name: Name of the property to get
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}

    value = get_project_property(current_project, property_name)
    return {property_name: value}


@tool()
def set_project_property_tool(property_name: str, property_value: Any) -> Dict[str, Any]:
    """Set a project property value.

    Args:
        property_name: Name of the property to set
        property_value: Value to set for the property
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    result = set_project_property(current_project, property_name, property_value)

    if result:
        return success_response(
            {"property_name": property_name, "property_value": property_value},
            message=f"Successfully set project property '{property_name}' to '{property_value}'",
        )
    else:
        return error_response(
            "OPERATION_FAILED",
            f"Failed to set project property '{property_name}'",
            context={"property_name": property_name, "property_value": property_value},
        )


@resource("resolve://project/timeline-format")
def get_timeline_format() -> Dict[str, Any]:
    """Get timeline format settings for the current project."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}

    return get_timeline_format_settings(current_project)


@tool()
def set_timeline_format_tool(width: int, height: int, frame_rate: float, interlaced: bool = False) -> Dict[str, Any]:
    """Set timeline format (resolution and frame rate).

    Args:
        width: Timeline width in pixels
        height: Timeline height in pixels
        frame_rate: Timeline frame rate
        interlaced: Whether the timeline should use interlaced processing
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    result = set_timeline_format(current_project, width, height, frame_rate, interlaced)

    if result:
        interlace_status = "interlaced" if interlaced else "progressive"
        return success_response(
            {"width": width, "height": height, "frame_rate": frame_rate, "interlaced": interlaced},
            message=f"Successfully set timeline format to {width}x{height} at {frame_rate} fps ({interlace_status})",
        )
    else:
        return error_response(
            "OPERATION_FAILED",
            "Failed to set timeline format",
            context={"width": width, "height": height, "frame_rate": frame_rate, "interlaced": interlaced},
        )


@resource("resolve://project/superscale")
def get_superscale_settings_endpoint() -> Dict[str, Any]:
    """Get SuperScale settings for the current project."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}

    return get_superscale_settings(current_project)


@tool()
def set_superscale_settings_tool(enabled: bool, quality: int = 0) -> Dict[str, Any]:
    """Set SuperScale settings for the current project.

    Args:
        enabled: Whether SuperScale is enabled
        quality: SuperScale quality (0=Auto, 1=Better Quality, 2=Smoother)
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    quality_names = {0: "Auto", 1: "Better Quality", 2: "Smoother"}

    result = set_superscale_settings(current_project, enabled, quality)

    if result:
        status = "enabled" if enabled else "disabled"
        quality_name = quality_names.get(quality, "Unknown")
        return success_response(
            {"enabled": enabled, "quality": quality, "quality_name": quality_name},
            message=f"Successfully {status} SuperScale with quality set to {quality_name}",
        )
    else:
        return error_response(
            "OPERATION_FAILED", "Failed to set SuperScale settings", context={"enabled": enabled, "quality": quality}
        )


@resource("resolve://project/color-settings")
def get_color_settings_endpoint() -> Dict[str, Any]:
    """Get color science and color space settings for the current project."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}

    return get_color_settings(current_project)


@tool()
def set_color_science_mode_tool(mode: str) -> Dict[str, Any]:
    """Set color science mode for the current project.

    Args:
        mode: Color science mode ('YRGB', 'YRGB Color Managed', 'ACEScct', or numeric value)
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    result = set_color_science_mode(current_project, mode)

    if result:
        return success_response({"mode": mode}, message=f"Successfully set color science mode to '{mode}'")
    else:
        return error_response(
            "OPERATION_FAILED", f"Failed to set color science mode to '{mode}'", context={"mode": mode}
        )


@tool()
def set_color_space_tool(color_space: str, gamma: str = None) -> Dict[str, Any]:
    """Set timeline color space and gamma.

    Args:
        color_space: Timeline color space (e.g., 'Rec.709', 'DCI-P3 D65', 'Rec.2020')
        gamma: Timeline gamma (e.g., 'Rec.709 Gamma', 'Gamma 2.4')
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    result = set_color_space(current_project, color_space, gamma)

    if result:
        if gamma:
            return success_response(
                {"color_space": color_space, "gamma": gamma},
                message=f"Successfully set timeline color space to '{color_space}' with gamma '{gamma}'",
            )
        else:
            return success_response(
                {"color_space": color_space}, message=f"Successfully set timeline color space to '{color_space}'"
            )
    else:
        return error_response(
            "OPERATION_FAILED",
            "Failed to set timeline color space",
            context={"color_space": color_space, "gamma": gamma},
        )


@resource("resolve://project/metadata")
def get_project_metadata_endpoint() -> Dict[str, Any]:
    """Get metadata for the current project."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}

    return get_project_metadata(current_project)


@resource("resolve://project/info")
def get_project_info_endpoint() -> Dict[str, Any]:
    """Get comprehensive information about the current project."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}

    return get_project_info(current_project)


def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
