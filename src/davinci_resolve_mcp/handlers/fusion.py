"""Handlers for Fusion composition effects and generators."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers
from davinci_resolve_mcp.utils.response import success_response, error_response

logger = logging.getLogger("davinci-resolve-mcp.fusion")
registry = HandlerRegistry()
resource = registry.resource
tool = registry.tool
resolve: Optional[Any] = None


@tool()
def add_fusion_effect(timeline_item_id: str, effect_name: str, settings: Dict[str, Any] = None) -> Dict[str, Any]:
    """Add a Fusion effect (or adjust existing nodes) on a TimelineItem.

    Args:
        timeline_item_id: The ID of the timeline item (or unique name)
        effect_name: The Fusion tool name (e.g. "Vignette", "CameraShake", "BrightnessContrast")
        settings: Dictionary of settings to apply to the tool (e.g. {"Gain": 2.0})
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )
    try:
        from davinci_resolve_mcp.api.fusion_operations import add_fusion_effect as add_fusion_effect_func

        result = add_fusion_effect_func(resolve, timeline_item_id, effect_name, settings)
        if isinstance(result, str) and result.startswith("Error"):
            return error_response(
                "OPERATION_FAILED", result, context={"timeline_item_id": timeline_item_id, "effect_name": effect_name}
            )
        return success_response(
            {"result": result},
            message=f"Added fusion effect '{effect_name}'",
            context={"timeline_item_id": timeline_item_id, "effect_name": effect_name},
        )
    except Exception as e:
        logger.error("Error adding fusion effect: %s", e, exc_info=True)
        return error_response(
            "OPERATION_FAILED",
            f"Error adding fusion effect: {e}",
            context={"timeline_item_id": timeline_item_id, "effect_name": effect_name},
        )


@tool()
def add_fusion_generator(timeline_item_id: str, generator_name: str, settings: Dict[str, Any] = None) -> Dict[str, Any]:
    """Add a Fusion generator (Text+, Background) via Merge on a TimelineItem.

    Args:
        timeline_item_id: The ID of the timeline item (or unique name)
        generator_name: The Fusion tool name (e.g. "TextPlus")
        settings: Dictionary of settings to apply to the tool
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )
    try:
        from davinci_resolve_mcp.api.fusion_operations import add_fusion_generator as add_gen_func

        result = add_gen_func(resolve, timeline_item_id, generator_name, settings)
        if isinstance(result, str) and result.startswith("Error"):
            return error_response(
                "OPERATION_FAILED",
                result,
                context={"timeline_item_id": timeline_item_id, "generator_name": generator_name},
            )
        return success_response(
            {"result": result},
            message=f"Added fusion generator '{generator_name}'",
            context={"timeline_item_id": timeline_item_id, "generator_name": generator_name},
        )
    except Exception as e:
        logger.error("Error adding fusion generator: %s", e, exc_info=True)
        return error_response(
            "OPERATION_FAILED",
            f"Error adding fusion generator: {e}",
            context={"timeline_item_id": timeline_item_id, "generator_name": generator_name},
        )


def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
