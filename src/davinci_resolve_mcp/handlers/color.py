"""Handlers for color page resources and grading helpers."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers
from davinci_resolve_mcp.utils.response import success_response, error_response

logger = logging.getLogger("davinci-resolve-mcp.color")
registry = HandlerRegistry()
resource = registry.resource
tool = registry.tool
resolve: Optional[Any] = None


@resource("resolve://color/current-node")
def get_current_color_node() -> Dict[str, Any]:
    """Get information about the current node in the color page."""
    from davinci_resolve_mcp.api.color_operations import get_current_node as get_node_func

    return get_node_func(resolve)


@resource("resolve://color/wheels/{node_index}")
def get_color_wheel_params(node_index: int = None) -> Dict[str, Any]:
    """Get color wheel parameters for a specific node.

    Args:
        node_index: Index of the node to get color wheels from (uses current node if None)
    """
    from davinci_resolve_mcp.api.color_operations import get_color_wheels as get_wheels_func

    return get_wheels_func(resolve, node_index)


@tool()
def apply_lut(lut_path: str, node_index: int = None) -> Dict[str, Any]:
    """Apply a LUT to a node in the color page.

    Args:
        lut_path: Path to the LUT file to apply
        node_index: Index of the node to apply the LUT to (uses current node if None)
    """
    from davinci_resolve_mcp.api.color_operations import apply_lut as apply_lut_func

    result = apply_lut_func(resolve, lut_path, node_index)
    if isinstance(result, str):
        if result.startswith("Error:"):
            return error_response("OPERATION_FAILED", result[7:].strip())
        elif result.startswith("Failed"):
            return error_response("OPERATION_FAILED", result)
        else:
            return success_response(message=result, context={"lut_path": lut_path, "node_index": node_index})
    return success_response(data=result, context={"lut_path": lut_path, "node_index": node_index})


@tool()
def set_color_wheel_param(wheel: str, param: str, value: float, node_index: int = None) -> Dict[str, Any]:
    """Set a color wheel parameter for a node.

    Args:
        wheel: Which color wheel to adjust ('lift', 'gamma', 'gain', 'offset')
        param: Which parameter to adjust ('red', 'green', 'blue', 'master')
        value: The value to set (typically between -1.0 and 1.0)
        node_index: Index of the node to set parameter for (uses current node if None)
    """
    from davinci_resolve_mcp.api.color_operations import set_color_wheel_param as set_param_func

    result = set_param_func(resolve, wheel, param, value, node_index)
    if isinstance(result, str):
        if result.startswith("Error:"):
            return error_response("OPERATION_FAILED", result[7:].strip())
        elif result.startswith("Failed"):
            return error_response("OPERATION_FAILED", result)
        else:
            return success_response(
                message=result,
                context={"wheel": wheel, "param": param, "value": value, "node_index": node_index},
            )
    return success_response(
        data=result, context={"wheel": wheel, "param": param, "value": value, "node_index": node_index}
    )


@tool()
def add_node(node_type: str = "serial", label: str = None) -> Dict[str, Any]:
    """Add a new node to the current grade in the color page.

    Args:
        node_type: Type of node to add. Options: 'serial', 'parallel', 'layer'
        label: Optional label/name for the new node
    """
    from davinci_resolve_mcp.api.color_operations import add_node as add_node_func

    result = add_node_func(resolve, node_type, label)
    if isinstance(result, str):
        if result.startswith("Error:"):
            return error_response("OPERATION_FAILED", result[7:].strip())
        elif result.startswith("Failed"):
            return error_response("OPERATION_FAILED", result)
        else:
            return success_response(message=result, context={"node_type": node_type, "label": label})
    return success_response(data=result, context={"node_type": node_type, "label": label})


@tool()
def copy_grade(source_clip_name: str = None, target_clip_name: str = None, mode: str = "full") -> Dict[str, Any]:
    """Copy a grade from one clip to another in the color page.

    Args:
        source_clip_name: Name of the source clip to copy grade from (uses current clip if None)
        target_clip_name: Name of the target clip to apply grade to (uses current clip if None)
        mode: What to copy - 'full' (entire grade), 'current_node', or 'all_nodes'
    """
    from davinci_resolve_mcp.api.color_operations import copy_grade as copy_grade_func

    result = copy_grade_func(resolve, source_clip_name, target_clip_name, mode)
    if isinstance(result, str):
        if result.startswith("Error:"):
            return error_response("OPERATION_FAILED", result[7:].strip())
        elif result.startswith("Failed"):
            return error_response("OPERATION_FAILED", result)
        else:
            return success_response(
                message=result,
                context={"source_clip": source_clip_name, "target_clip": target_clip_name, "mode": mode},
            )
    return success_response(
        data=result, context={"source_clip": source_clip_name, "target_clip": target_clip_name, "mode": mode}
    )


def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
