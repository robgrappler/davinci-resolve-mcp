"""Handlers for object inspection helpers exposed via MCP."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers
from davinci_resolve_mcp.utils.object_inspection import (
    inspect_object,
    print_object_help,
)

logger = logging.getLogger("davinci-resolve-mcp.inspection")
registry = HandlerRegistry()
resource = registry.resource
tool = registry.tool
resolve: Optional[Any] = None

@resource("resolve://inspect/resolve")
def inspect_resolve_object() -> Dict[str, Any]:
    """Inspect the main resolve object and return its methods and properties."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    return inspect_object(resolve)

@resource("resolve://inspect/project-manager")
def inspect_project_manager_object() -> Dict[str, Any]:
    """Inspect the project manager object and return its methods and properties."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    return inspect_object(project_manager)

@resource("resolve://inspect/current-project")
def inspect_current_project_object() -> Dict[str, Any]:
    """Inspect the current project object and return its methods and properties."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    return inspect_object(current_project)

@resource("resolve://inspect/media-pool")
def inspect_media_pool_object() -> Dict[str, Any]:
    """Inspect the media pool object and return its methods and properties."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return {"error": "Failed to get Media Pool"}
    
    return inspect_object(media_pool)

@resource("resolve://inspect/current-timeline")
def inspect_current_timeline_object() -> Dict[str, Any]:
    """Inspect the current timeline object and return its methods and properties."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}
    
    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return {"error": "No timeline currently active"}
    
    return inspect_object(current_timeline)

@tool()
def object_help(object_type: str) -> str:
    """
    Get human-readable help for a DaVinci Resolve API object.
    
    Args:
        object_type: Type of object to get help for ('resolve', 'project_manager', 
                     'project', 'media_pool', 'timeline', 'media_storage')
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    # Map object type string to actual object
    obj = None
    
    if object_type == 'resolve':
        obj = resolve
    elif object_type == 'project_manager':
        obj = resolve.GetProjectManager()
    elif object_type == 'project':
        pm = resolve.GetProjectManager()
        if pm:
            obj = pm.GetCurrentProject()
    elif object_type == 'media_pool':
        pm = resolve.GetProjectManager()
        if pm:
            project = pm.GetCurrentProject()
            if project:
                obj = project.GetMediaPool()
    elif object_type == 'timeline':
        pm = resolve.GetProjectManager()
        if pm:
            project = pm.GetCurrentProject()
            if project:
                obj = project.GetCurrentTimeline()
    elif object_type == 'media_storage':
        obj = resolve.GetMediaStorage()
    else:
        return f"Error: Unknown object type '{object_type}'"
    
    if obj is None:
        return f"Error: Failed to get {object_type} object"
    
    # Generate and return help text
    return print_object_help(obj)

@tool()
def inspect_custom_object(object_path: str) -> Dict[str, Any]:
    """
    Inspect a custom DaVinci Resolve API object by path.
    
    Args:
        object_path: Path to the object using dot notation (e.g., 'resolve.GetMediaStorage()')
    """
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}
    
    try:
        # Start with resolve object
        obj = resolve
        
        # Split the path and traverse down
        parts = object_path.split('.')
        
        # Skip the first part if it's 'resolve'
        start_index = 1 if parts[0].lower() == 'resolve' else 0
        
        for i in range(start_index, len(parts)):
            part = parts[i]
            
            # Check if it's a method call
            if part.endswith('()'):
                method_name = part[:-2]
                if hasattr(obj, method_name) and callable(getattr(obj, method_name)):
                    obj = getattr(obj, method_name)()
                else:
                    return {"error": f"Method '{method_name}' not found or not callable"}
            else:
                # It's an attribute access
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                else:
                    return {"error": f"Attribute '{part}' not found"}
        
        # Inspect the object we've retrieved
        return inspect_object(obj)
    except Exception as e:
        return {"error": f"Error inspecting object: {str(e)}"}

def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
