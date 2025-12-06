"""Handlers for timeline inspection and creation handlers."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers

logger = logging.getLogger("davinci-resolve-mcp.timelines")
registry = HandlerRegistry()
resource = registry.resource
tool = registry.tool
resolve: Optional[Any] = None

@resource("resolve://timelines")
def list_timelines() -> List[str]:
    """List all timelines in the current project."""
    logger.info("Received request to list timelines")
    
    if resolve is None:
        logger.error("Not connected to DaVinci Resolve")
        return ["Error: Not connected to DaVinci Resolve"]
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        logger.error("Failed to get Project Manager")
        return ["Error: Failed to get Project Manager"]
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        logger.error("No project currently open")
        return ["Error: No project currently open"]
    
    timeline_count = current_project.GetTimelineCount()
    logger.info(f"Timeline count: {timeline_count}")
    
    timelines = []
    
    for i in range(1, timeline_count + 1):
        timeline = current_project.GetTimelineByIndex(i)
        if timeline:
            timeline_name = timeline.GetName()
            timelines.append(timeline_name)
            logger.info(f"Found timeline {i}: {timeline_name}")
    
    if not timelines:
        logger.info("No timelines found in the current project")
        return ["No timelines found in the current project"]
    
    logger.info(f"Returning {len(timelines)} timelines: {', '.join(timelines)}")
    return timelines

@resource("resolve://current-timeline")
def get_current_timeline() -> Dict[str, Any]:
    """Get information about the current timeline."""
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
    
    # Get basic timeline information
    result = {
        "name": current_timeline.GetName(),
        "fps": current_timeline.GetSetting("timelineFrameRate"),
        "resolution": {
            "width": current_timeline.GetSetting("timelineResolutionWidth"),
            "height": current_timeline.GetSetting("timelineResolutionHeight")
        },
        "duration": current_timeline.GetEndFrame() - current_timeline.GetStartFrame() + 1
    }
    
    return result

@resource("resolve://timeline-tracks/{timeline_name}")
def get_timeline_tracks(timeline_name: str = None) -> Dict[str, Any]:
    """Get the track structure of a timeline.
    
    Args:
        timeline_name: Optional name of the timeline to get tracks from. Uses current timeline if None.
    """
    from api.timeline_operations import get_timeline_tracks as get_tracks_func
    return get_tracks_func(resolve, timeline_name)

@tool()
def create_timeline(name: str) -> str:
    """Create a new timeline with the given name.
    
    Args:
        name: The name for the new timeline
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not name:
        return "Error: Timeline name cannot be empty"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    timeline = media_pool.CreateEmptyTimeline(name)
    if timeline:
        return f"Successfully created timeline '{name}'"
    else:
        return f"Failed to create timeline '{name}'"

@tool()
def create_empty_timeline(name: str, 
                       frame_rate: str = None, 
                       resolution_width: int = None, 
                       resolution_height: int = None,
                       start_timecode: str = None,
                       video_tracks: int = None,
                       audio_tracks: int = None) -> str:
    """Create a new timeline with the given name and custom settings.
    
    Args:
        name: The name for the new timeline
        frame_rate: Optional frame rate (e.g. "24", "29.97", "30", "60")
        resolution_width: Optional width in pixels (e.g. 1920)
        resolution_height: Optional height in pixels (e.g. 1080)
        start_timecode: Optional start timecode (e.g. "01:00:00:00")
        video_tracks: Optional number of video tracks (Default is project setting)
        audio_tracks: Optional number of audio tracks (Default is project setting)
    """
    from api.timeline_operations import create_empty_timeline as create_empty_timeline_func
    return create_empty_timeline_func(resolve, name, frame_rate, resolution_width, 
                                    resolution_height, start_timecode, 
                                    video_tracks, audio_tracks)

@tool()
def delete_timeline(name: str) -> str:
    """Delete a timeline by name.
    
    Args:
        name: The name of the timeline to delete
    """
    from api.timeline_operations import delete_timeline as delete_timeline_func
    return delete_timeline_func(resolve, name)

@tool()
def set_current_timeline(name: str) -> str:
    """Switch to a timeline by name.
    
    Args:
        name: The name of the timeline to set as current
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    if not name:
        return "Error: Timeline name cannot be empty"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    # Find the timeline by name
    timeline_count = current_project.GetTimelineCount()
    for i in range(1, timeline_count + 1):
        timeline = current_project.GetTimelineByIndex(i)
        if timeline and timeline.GetName() == name:
            result = current_project.SetCurrentTimeline(timeline)
            if result:
                return f"Successfully switched to timeline '{name}'"
            else:
                return f"Failed to switch to timeline '{name}'"
    
    return f"Error: Timeline '{name}' not found"

@tool()
def add_marker(frame: int = None, color: str = "Blue", note: str = "") -> str:
    """Add a marker at the specified frame in the current timeline.
    
    Args:
        frame: The frame number to add the marker at (defaults to current position if None)
        color: The marker color (Blue, Cyan, Green, Yellow, Red, Pink, Purple, Fuchsia, Rose, Lavender, Sky, Mint, Lemon, Sand, Cocoa, Cream)
        note: Text note to add to the marker
    """
    from api.timeline_operations import add_marker as add_marker_func
    return add_marker_func(resolve, frame, color, note)

def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
