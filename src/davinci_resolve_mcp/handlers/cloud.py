"""Handlers for Blackmagic Cloud project helpers."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers
from davinci_resolve_mcp.utils.cloud_operations import (
    create_cloud_project,
    import_cloud_project,
    restore_cloud_project,
    get_cloud_project_list,
    export_project_to_cloud,
    add_user_to_cloud_project,
    remove_user_from_cloud_project,
)

logger = logging.getLogger("davinci-resolve-mcp.cloud")
registry = HandlerRegistry()
resource = registry.resource
tool = registry.tool
resolve: Optional[Any] = None


@resource("resolve://cloud/projects")
def get_cloud_projects() -> Dict[str, Any]:
    """Get list of available cloud projects."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "success": False}

    return get_cloud_project_list(resolve)


@tool()
def create_cloud_project_tool(project_name: str, folder_path: str = None) -> Dict[str, Any]:
    """Create a new cloud project.

    Args:
        project_name: Name for the new cloud project
        folder_path: Optional path for the cloud project folder
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "success": False}

    return create_cloud_project(resolve, project_name, folder_path)


@tool()
def import_cloud_project_tool(cloud_id: str, project_name: str = None) -> Dict[str, Any]:
    """Import a project from DaVinci Resolve cloud.

    Args:
        cloud_id: Cloud ID or reference of the project to import
        project_name: Optional custom name for the imported project (uses original name if None)
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "success": False}

    return import_cloud_project(resolve, cloud_id, project_name)


@tool()
def restore_cloud_project_tool(cloud_id: str, project_name: str = None) -> Dict[str, Any]:
    """Restore a project from DaVinci Resolve cloud.

    Args:
        cloud_id: Cloud ID or reference of the project to restore
        project_name: Optional custom name for the restored project (uses original name if None)
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "success": False}

    return restore_cloud_project(resolve, cloud_id, project_name)


@tool()
def export_project_to_cloud_tool(project_name: str = None) -> Dict[str, Any]:
    """Export current or specified project to DaVinci Resolve cloud.

    Args:
        project_name: Optional name of project to export (uses current project if None)
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "success": False}

    return export_project_to_cloud(resolve, project_name)


@tool()
def add_user_to_cloud_project_tool(cloud_id: str, user_email: str, permissions: str = "viewer") -> Dict[str, Any]:
    """Add a user to a cloud project with specified permissions.

    Args:
        cloud_id: Cloud ID of the project
        user_email: Email of the user to add
        permissions: Permission level (viewer, editor, admin)
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "success": False}

    return add_user_to_cloud_project(resolve, cloud_id, user_email, permissions)


@tool()
def remove_user_from_cloud_project_tool(cloud_id: str, user_email: str) -> Dict[str, Any]:
    """Remove a user from a cloud project.

    Args:
        cloud_id: Cloud ID of the project
        user_email: Email of the user to remove
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve", "success": False}

    return remove_user_from_cloud_project(resolve, cloud_id, user_email)


def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
