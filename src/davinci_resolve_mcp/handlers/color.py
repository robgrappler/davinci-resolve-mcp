"""Handlers for color page resources and grading helpers."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers

logger = logging.getLogger("davinci-resolve-mcp.color")
registry = HandlerRegistry()
resource = registry.resource
tool = registry.tool
resolve: Optional[Any] = None


@resource("resolve://color/current-node")
def get_current_color_node() -> Dict[str, Any]:
    """Get information about the current node in the color page."""
    from api.color_operations import get_current_node as get_node_func

    return get_node_func(resolve)


@resource("resolve://color/wheels/{node_index}")
def get_color_wheel_params(node_index: int = None) -> Dict[str, Any]:
    """Get color wheel parameters for a specific node.

    Args:
        node_index: Index of the node to get color wheels from (uses current node if None)
    """
    from api.color_operations import get_color_wheels as get_wheels_func

    return get_wheels_func(resolve, node_index)


@tool()
def apply_lut(lut_path: str, node_index: int = None) -> str:
    """Apply a LUT to a node in the color page.

    Args:
        lut_path: Path to the LUT file to apply
        node_index: Index of the node to apply the LUT to (uses current node if None)
    """
    from api.color_operations import apply_lut as apply_lut_func

    return apply_lut_func(resolve, lut_path, node_index)


@tool()
def set_color_wheel_param(wheel: str, param: str, value: float, node_index: int = None) -> str:
    """Set a color wheel parameter for a node.

    Args:
        wheel: Which color wheel to adjust ('lift', 'gamma', 'gain', 'offset')
        param: Which parameter to adjust ('red', 'green', 'blue', 'master')
        value: The value to set (typically between -1.0 and 1.0)
        node_index: Index of the node to set parameter for (uses current node if None)
    """
    from api.color_operations import set_color_wheel_param as set_param_func

    return set_param_func(resolve, wheel, param, value, node_index)


@tool()
def add_node(node_type: str = "serial", label: str = None) -> str:
    """Add a new node to the current grade in the color page.

    Args:
        node_type: Type of node to add. Options: 'serial', 'parallel', 'layer'
        label: Optional label/name for the new node
    """
    from api.color_operations import add_node as add_node_func

    return add_node_func(resolve, node_type, label)


@tool()
def copy_grade(source_clip_name: str = None, target_clip_name: str = None, mode: str = "full") -> str:
    """Copy a grade from one clip to another in the color page.

    Args:
        source_clip_name: Name of the source clip to copy grade from (uses current clip if None)
        target_clip_name: Name of the target clip to apply grade to (uses current clip if None)
        mode: What to copy - 'full' (entire grade), 'current_node', or 'all_nodes'
    """
    from api.color_operations import copy_grade as copy_grade_func

    return copy_grade_func(resolve, source_clip_name, target_clip_name, mode)


def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
