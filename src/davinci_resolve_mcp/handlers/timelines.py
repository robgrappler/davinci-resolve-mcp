"""Handlers for timeline inspection and creation handlers."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers
from davinci_resolve_mcp.utils.response import success_response, error_response

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
            "height": current_timeline.GetSetting("timelineResolutionHeight"),
        },
        "duration": current_timeline.GetEndFrame() - current_timeline.GetStartFrame() + 1,
    }

    return result


@resource("resolve://timeline-tracks/{timeline_name}")
def get_timeline_tracks(timeline_name: str = None) -> Dict[str, Any]:
    """Get the track structure of a timeline.

    Args:
        timeline_name: Optional name of the timeline to get tracks from. Uses current timeline if None.
    """
    from davinci_resolve_mcp.api.timeline_operations import get_timeline_tracks as get_tracks_func

    return get_tracks_func(resolve, timeline_name)


@tool()
def create_timeline(name: str) -> Dict[str, Any]:
    """Create a new timeline with the given name.

    Args:
        name: The name for the new timeline
    """
    if resolve is None:
        return error_response("NOT_CONNECTED", "Not connected to DaVinci Resolve")

    if not name:
        return error_response("INVALID_ARG", "Timeline name cannot be empty")

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return error_response("OPERATION_FAILED", "Failed to get Media Pool")

    timeline = media_pool.CreateEmptyTimeline(name)
    if timeline:
        return success_response(message=f"Created timeline '{name}'", context={"timeline_name": name})
    else:
        return error_response("OPERATION_FAILED", f"Failed to create timeline '{name}'")


@tool()
def create_empty_timeline(
    name: str,
    frame_rate: str = None,
    resolution_width: int = None,
    resolution_height: int = None,
    start_timecode: str = None,
    video_tracks: int = None,
    audio_tracks: int = None,
) -> Dict[str, Any]:
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
    from davinci_resolve_mcp.api.timeline_operations import create_empty_timeline as create_empty_timeline_func

    result = create_empty_timeline_func(
        resolve, name, frame_rate, resolution_width, resolution_height, start_timecode, video_tracks, audio_tracks
    )
    if result.startswith("Error:"):
        return error_response("OPERATION_FAILED", result[7:].strip())
    elif result.startswith("Failed"):
        return error_response("OPERATION_FAILED", result)
    else:
        return success_response(message=result, context={"timeline_name": name})


@tool()
def delete_timeline(name: str) -> Dict[str, Any]:
    """Delete a timeline by name.

    Args:
        name: The name of the timeline to delete
    """
    from davinci_resolve_mcp.api.timeline_operations import delete_timeline as delete_timeline_func

    result = delete_timeline_func(resolve, name)
    if result.startswith("Error:"):
        return error_response("OPERATION_FAILED", result[7:].strip())
    elif result.startswith("Failed"):
        return error_response("OPERATION_FAILED", result)
    else:
        return success_response(message=result, context={"timeline_name": name})


@tool()
def set_current_timeline(name: str) -> Dict[str, Any]:
    """Switch to a timeline by name.

    Args:
        name: The name of the timeline to set as current
    """
    if resolve is None:
        return error_response("NOT_CONNECTED", "Not connected to DaVinci Resolve")

    if not name:
        return error_response("INVALID_ARG", "Timeline name cannot be empty")

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    # Find the timeline by name
    timeline_count = current_project.GetTimelineCount()
    for i in range(1, timeline_count + 1):
        timeline = current_project.GetTimelineByIndex(i)
        if timeline and timeline.GetName() == name:
            result = current_project.SetCurrentTimeline(timeline)
            if result:
                return success_response(message=f"Switched to timeline '{name}'", context={"timeline_name": name})
            else:
                return error_response("OPERATION_FAILED", f"Failed to switch to timeline '{name}'")

    return error_response("NOT_FOUND", f"Timeline '{name}' not found")


@tool()
def add_marker(frame: int = None, color: str = "Blue", note: str = "") -> Dict[str, Any]:
    """Add a marker at the specified frame in the current timeline.

    Args:
        frame: The frame number to add the marker at (defaults to current position if None)
        color: The marker color (Blue, Cyan, Green, Yellow, Red, Pink, Purple, Fuchsia, Rose, Lavender, Sky, Mint, Lemon, Sand, Cocoa, Cream)
        note: Text note to add to the marker
    """
    from davinci_resolve_mcp.api.timeline_operations import add_marker as add_marker_func

    result = add_marker_func(resolve, frame, color, note)
    if result.startswith("Error:"):
        return error_response("OPERATION_FAILED", result[7:].strip())
    elif result.startswith("Failed"):
        return error_response("OPERATION_FAILED", result)
    else:
        return success_response(message=result, context={"frame": frame, "color": color, "note": note})


@tool()
def set_current_frame(frame: int) -> Dict[str, Any]:
    """Set the current playhead position to a specific frame.

    Args:
        frame: The frame number to move the playhead to
    """
    if resolve is None:
        return error_response("NOT_CONNECTED", "Not connected to DaVinci Resolve")

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return error_response("NO_TIMELINE", "No timeline currently active")

    from davinci_resolve_mcp.api.timeline_operations import set_current_frame as set_current_frame_func

    result = set_current_frame_func(resolve, frame)
    if result.startswith("Error:"):
        return error_response("OPERATION_FAILED", result[7:].strip())
    elif result.startswith("Failed"):
        return error_response("OPERATION_FAILED", result)
    else:
        return success_response(message=result, context={"frame": frame})


@tool()
def razor_timeline(frame: int = None) -> Dict[str, Any]:
    """Cut all clips at the current playhead position or a specified frame.

    Args:
        frame: The frame number to make the cut at (defaults to current playhead position if None)
    """
    from davinci_resolve_mcp.api.timeline_operations import razor_timeline as razor_timeline_func

    result = razor_timeline_func(resolve, frame)
    if result.startswith("Error:") or result.startswith("Aborted"):
        return error_response("OPERATION_FAILED", result)
    elif result.startswith("Failed"):
        return error_response("OPERATION_FAILED", result)
    else:
        return success_response(message=result, context={"frame": frame})


def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
