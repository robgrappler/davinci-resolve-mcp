"""Handlers for timeline item inspection and manipulation handlers."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers
from davinci_resolve_mcp.utils.response import success_response, error_response

logger = logging.getLogger("davinci-resolve-mcp.timeline_items")
registry = HandlerRegistry()
resource = registry.resource
tool = registry.tool
resolve: Optional[Any] = None


@resource("resolve://timeline-item/{timeline_item_id}")
def get_timeline_item_properties(timeline_item_id: str) -> Dict[str, Any]:
    """Get properties of a specific timeline item by ID.

    Args:
        timeline_item_id: The ID of the timeline item to get properties for
    """
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

    try:
        # Find the timeline item by ID
        # We'll need to get all items from all tracks and check their IDs
        video_track_count = current_timeline.GetTrackCount("video")
        audio_track_count = current_timeline.GetTrackCount("audio")

        timeline_item = None

        # Search video tracks
        for track_index in range(1, video_track_count + 1):
            items = current_timeline.GetItemListInTrack("video", track_index)
            if items:
                for item in items:
                    if str(item.GetUniqueId()) == timeline_item_id:
                        timeline_item = item
                        break
            if timeline_item:
                break

        # If not found, search audio tracks
        if not timeline_item:
            for track_index in range(1, audio_track_count + 1):
                items = current_timeline.GetItemListInTrack("audio", track_index)
                if items:
                    for item in items:
                        if str(item.GetUniqueId()) == timeline_item_id:
                            timeline_item = item
                            break
                if timeline_item:
                    break

        if not timeline_item:
            return {"error": f"Timeline item with ID '{timeline_item_id}' not found"}

        # Get basic properties
        properties = {
            "id": timeline_item_id,
            "name": timeline_item.GetName(),
            "type": timeline_item.GetType(),
            "start_frame": timeline_item.GetStart(),
            "end_frame": timeline_item.GetEnd(),
            "duration": timeline_item.GetDuration(),
        }

        # Get additional properties if it's a video item
        if timeline_item.GetType() == "Video":
            # Transform properties
            properties["transform"] = {
                "position": {"x": timeline_item.GetProperty("Pan"), "y": timeline_item.GetProperty("Tilt")},
                "zoom": timeline_item.GetProperty("ZoomX"),  # ZoomX/ZoomY can be different for non-uniform scaling
                "zoom_x": timeline_item.GetProperty("ZoomX"),
                "zoom_y": timeline_item.GetProperty("ZoomY"),
                "rotation": timeline_item.GetProperty("Rotation"),
                "anchor_point": {
                    "x": timeline_item.GetProperty("AnchorPointX"),
                    "y": timeline_item.GetProperty("AnchorPointY"),
                },
                "pitch": timeline_item.GetProperty("Pitch"),
                "yaw": timeline_item.GetProperty("Yaw"),
            }

            # Crop properties
            properties["crop"] = {
                "left": timeline_item.GetProperty("CropLeft"),
                "right": timeline_item.GetProperty("CropRight"),
                "top": timeline_item.GetProperty("CropTop"),
                "bottom": timeline_item.GetProperty("CropBottom"),
            }

            # Composite properties
            properties["composite"] = {
                "mode": timeline_item.GetProperty("CompositeMode"),
                "opacity": timeline_item.GetProperty("Opacity"),
            }

            # Dynamic zoom properties
            properties["dynamic_zoom"] = {
                "enabled": timeline_item.GetProperty("DynamicZoomEnable"),
                "mode": timeline_item.GetProperty("DynamicZoomMode"),
            }

            # Retime properties
            properties["retime"] = {
                "speed": timeline_item.GetProperty("Speed"),
                "process": timeline_item.GetProperty("RetimeProcess"),
            }

            # Stabilization properties
            properties["stabilization"] = {
                "enabled": timeline_item.GetProperty("StabilizationEnable"),
                "method": timeline_item.GetProperty("StabilizationMethod"),
                "strength": timeline_item.GetProperty("StabilizationStrength"),
            }

        # Audio-specific properties
        if timeline_item.GetType() == "Audio" or timeline_item.GetMediaType() == "Audio":
            properties["audio"] = {
                "volume": timeline_item.GetProperty("Volume"),
                "pan": timeline_item.GetProperty("Pan"),
                "eq_enabled": timeline_item.GetProperty("EQEnable"),
                "normalize_enabled": timeline_item.GetProperty("NormalizeEnable"),
                "normalize_level": timeline_item.GetProperty("NormalizeLevel"),
            }

        return properties

    except Exception as e:
        return {"error": f"Error getting timeline item properties: {str(e)}"}


@resource("resolve://timeline-items")
def get_timeline_items() -> List[Dict[str, Any]]:
    """Get all items in the current timeline with their IDs and basic properties."""
    if resolve is None:
        return [{"error": "Not connected to DaVinci Resolve"}]

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return [{"error": "Failed to get Project Manager"}]

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return [{"error": "No project currently open"}]

    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return [{"error": "No timeline currently active"}]

    try:
        # Get all tracks in the timeline
        video_track_count = current_timeline.GetTrackCount("video")
        audio_track_count = current_timeline.GetTrackCount("audio")

        items = []

        # Process video tracks
        for track_index in range(1, video_track_count + 1):
            track_items = current_timeline.GetItemListInTrack("video", track_index)
            if track_items:
                for item in track_items:
                    items.append(
                        {
                            "id": str(item.GetUniqueId()),
                            "name": item.GetName(),
                            "type": "video",
                            "track": track_index,
                            "start_frame": item.GetStart(),
                            "end_frame": item.GetEnd(),
                            "duration": item.GetDuration(),
                        }
                    )

        # Process audio tracks
        for track_index in range(1, audio_track_count + 1):
            track_items = current_timeline.GetItemListInTrack("audio", track_index)
            if track_items:
                for item in track_items:
                    items.append(
                        {
                            "id": str(item.GetUniqueId()),
                            "name": item.GetName(),
                            "type": "audio",
                            "track": track_index,
                            "start_frame": item.GetStart(),
                            "end_frame": item.GetEnd(),
                            "duration": item.GetDuration(),
                        }
                    )

        if not items:
            return [{"info": "No items found in the current timeline"}]

        return items
    except Exception as e:
        return [{"error": f"Error listing timeline items: {str(e)}"}]


@tool()
def set_timeline_item_transform(timeline_item_id: str, property_name: str, property_value: float) -> Dict[str, Any]:
    """Set a transform property for a timeline item.

    Args:
        timeline_item_id: The ID of the timeline item to modify
        property_name: The name of the property to set. Options include:
                      'Pan', 'Tilt', 'ZoomX', 'ZoomY', 'Rotation', 'AnchorPointX',
                      'AnchorPointY', 'Pitch', 'Yaw'
        property_value: The value to set for the property
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

    # Validate property name
    valid_properties = ["Pan", "Tilt", "ZoomX", "ZoomY", "Rotation", "AnchorPointX", "AnchorPointY", "Pitch", "Yaw"]

    if property_name not in valid_properties:
        return error_response("INVALID_ARG", f"Invalid property name. Must be one of: {', '.join(valid_properties)}")

    try:
        # Find the timeline item by ID
        video_track_count = current_timeline.GetTrackCount("video")

        timeline_item = None

        # Search video tracks
        for track_index in range(1, video_track_count + 1):
            items = current_timeline.GetItemListInTrack("video", track_index)
            if items:
                for item in items:
                    if str(item.GetUniqueId()) == timeline_item_id:
                        timeline_item = item
                        break
            if timeline_item:
                break

        if not timeline_item:
            return error_response("NOT_FOUND", f"Video timeline item with ID '{timeline_item_id}' not found")

        if timeline_item.GetType() != "Video":
            return error_response("INVALID_ARG", f"Timeline item with ID '{timeline_item_id}' is not a video item")

        # Set the property
        # DEBUG: Check if SetProperty exists and is callable
        func = getattr(timeline_item, "SetProperty", None)
        if not callable(func):
            return error_response(
                "OPERATION_FAILED",
                f"SetProperty is {type(func)} on item {type(timeline_item)} (ID: {timeline_item_id})",
            )

        try:
            result = func(property_name, property_value)
        except Exception as e:
            return error_response("OPERATION_FAILED", f"Error executing SetProperty: {e} (Type: {type(e)})")

        if result:
            return success_response(
                message=f"Set {property_name} to {property_value} for timeline item '{timeline_item.GetName()}'",
                context={
                    "timeline_item_id": timeline_item_id,
                    "property_name": property_name,
                    "property_value": property_value,
                },
            )
        else:
            try:
                name = timeline_item.GetName()
            except Exception:
                name = "Unknown"
            return error_response("OPERATION_FAILED", f"Failed to set {property_name} for timeline item '{name}'")
    except Exception as e:
        return error_response("OPERATION_FAILED", f"Error setting timeline item property: {str(e)}")


@tool()
def set_timeline_item_crop(timeline_item_id: str, crop_type: str, crop_value: float) -> Dict[str, Any]:
    """Set a crop property for a timeline item.

    Args:
        timeline_item_id: The ID of the timeline item to modify
        crop_type: The type of crop to set. Options: 'Left', 'Right', 'Top', 'Bottom'
        crop_value: The value to set for the crop (typically 0.0 to 1.0)
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

    # Validate crop type
    valid_crop_types = ["Left", "Right", "Top", "Bottom"]

    if crop_type not in valid_crop_types:
        return error_response("INVALID_ARG", f"Invalid crop type. Must be one of: {', '.join(valid_crop_types)}")

    property_name = f"Crop{crop_type}"

    try:
        # Find the timeline item by ID
        video_track_count = current_timeline.GetTrackCount("video")

        timeline_item = None

        # Search video tracks
        for track_index in range(1, video_track_count + 1):
            items = current_timeline.GetItemListInTrack("video", track_index)
            if items:
                for item in items:
                    if str(item.GetUniqueId()) == timeline_item_id:
                        timeline_item = item
                        break
            if timeline_item:
                break

        if not timeline_item:
            return error_response("NOT_FOUND", f"Video timeline item with ID '{timeline_item_id}' not found")

        if timeline_item.GetType() != "Video":
            return error_response("INVALID_ARG", f"Timeline item with ID '{timeline_item_id}' is not a video item")

        # Set the property
        result = timeline_item.SetProperty(property_name, crop_value)
        if result:
            return success_response(
                message=f"Set crop {crop_type.lower()} to {crop_value} for timeline item '{timeline_item.GetName()}'",
                context={"timeline_item_id": timeline_item_id, "crop_type": crop_type, "crop_value": crop_value},
            )
        else:
            return error_response(
                "OPERATION_FAILED",
                f"Failed to set crop {crop_type.lower()} for timeline item '{timeline_item.GetName()}'",
            )
    except Exception as e:
        return error_response("OPERATION_FAILED", f"Error setting timeline item crop: {str(e)}")


@tool()
def set_timeline_item_composite(
    timeline_item_id: str, composite_mode: str = None, opacity: float = None
) -> Dict[str, Any]:
    """Set composite properties for a timeline item.

    Args:
        timeline_item_id: The ID of the timeline item to modify
        composite_mode: Optional composite mode to set (e.g., 'Normal', 'Add', 'Multiply')
        opacity: Optional opacity value to set (0.0 to 1.0)
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

    # Validate inputs
    if composite_mode is None and opacity is None:
        return error_response("INVALID_ARG", "Must specify at least one of composite_mode or opacity")

    # Valid composite modes
    valid_composite_modes = [
        "Normal",
        "Add",
        "Subtract",
        "Difference",
        "Multiply",
        "Screen",
        "Overlay",
        "Hardlight",
        "Softlight",
        "Darken",
        "Lighten",
        "ColorDodge",
        "ColorBurn",
        "Exclusion",
        "Hue",
        "Saturation",
        "Color",
        "Luminosity",
    ]

    if composite_mode and composite_mode not in valid_composite_modes:
        return error_response(
            "INVALID_ARG", f"Invalid composite mode. Must be one of: {', '.join(valid_composite_modes)}"
        )

    if opacity is not None and (opacity < 0.0 or opacity > 1.0):
        return error_response("INVALID_ARG", "Opacity must be between 0.0 and 1.0")

    try:
        # Find the timeline item by ID
        video_track_count = current_timeline.GetTrackCount("video")

        timeline_item = None

        # Search video tracks
        for track_index in range(1, video_track_count + 1):
            items = current_timeline.GetItemListInTrack("video", track_index)
            if items:
                for item in items:
                    if str(item.GetUniqueId()) == timeline_item_id:
                        timeline_item = item
                        break
            if timeline_item:
                break

        if not timeline_item:
            return error_response("NOT_FOUND", f"Video timeline item with ID '{timeline_item_id}' not found")

        if timeline_item.GetType() != "Video":
            return error_response("INVALID_ARG", f"Timeline item with ID '{timeline_item_id}' is not a video item")

        op_success = True

        # Set composite mode if specified
        if composite_mode:
            result = timeline_item.SetProperty("CompositeMode", composite_mode)
            if not result:
                op_success = False

        # Set opacity if specified
        if opacity is not None:
            result = timeline_item.SetProperty("Opacity", opacity)
            if not result:
                op_success = False

        if op_success:
            changes = []
            if composite_mode:
                changes.append(f"composite mode to '{composite_mode}'")
            if opacity is not None:
                changes.append(f"opacity to {opacity}")

            return success_response(
                message=f"Set {' and '.join(changes)} for timeline item '{timeline_item.GetName()}'",
                context={"timeline_item_id": timeline_item_id, "composite_mode": composite_mode, "opacity": opacity},
            )
        else:
            return error_response(
                "OPERATION_FAILED",
                f"Failed to set some composite properties for timeline item '{timeline_item.GetName()}'",
            )
    except Exception as e:
        return error_response("OPERATION_FAILED", f"Error setting timeline item composite properties: {str(e)}")


@tool()
def set_timeline_item_retime(timeline_item_id: str, speed: float = None, process: str = None) -> Dict[str, Any]:
    """Set retiming properties for a timeline item.

    Args:
        timeline_item_id: The ID of the timeline item to modify
        speed: Optional speed factor (e.g., 0.5 for 50%, 2.0 for 200%)
        process: Optional retime process. Options: 'NearestFrame', 'FrameBlend', 'OpticalFlow'
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

    # Validate inputs
    if speed is None and process is None:
        return error_response("INVALID_ARG", "Must specify at least one of speed or process")

    if speed is not None and speed <= 0:
        return error_response("INVALID_ARG", "Speed must be greater than 0")

    valid_processes = ["NearestFrame", "FrameBlend", "OpticalFlow"]
    if process and process not in valid_processes:
        return error_response("INVALID_ARG", f"Invalid retime process. Must be one of: {', '.join(valid_processes)}")

    try:
        # Find the timeline item by ID
        video_track_count = current_timeline.GetTrackCount("video")

        timeline_item = None

        # Search video tracks
        for track_index in range(1, video_track_count + 1):
            items = current_timeline.GetItemListInTrack("video", track_index)
            if items:
                for item in items:
                    if str(item.GetUniqueId()) == timeline_item_id:
                        timeline_item = item
                        break
            if timeline_item:
                break

        if not timeline_item:
            return error_response("NOT_FOUND", f"Video timeline item with ID '{timeline_item_id}' not found")

        op_success = True

        # Set speed if specified
        if speed is not None:
            result = timeline_item.SetProperty("Speed", speed)
            if not result:
                op_success = False

        # Set retime process if specified
        if process:
            result = timeline_item.SetProperty("RetimeProcess", process)
            if not result:
                op_success = False

        if op_success:
            changes = []
            if speed is not None:
                changes.append(f"speed to {speed}x")
            if process:
                changes.append(f"retime process to '{process}'")

            return success_response(
                message=f"Set {' and '.join(changes)} for timeline item '{timeline_item.GetName()}'",
                context={"timeline_item_id": timeline_item_id, "speed": speed, "process": process},
            )
        else:
            return error_response(
                "OPERATION_FAILED",
                f"Failed to set some retime properties for timeline item '{timeline_item.GetName()}'",
            )
    except Exception as e:
        return error_response("OPERATION_FAILED", f"Error setting timeline item retime properties: {str(e)}")


@tool()
def set_timeline_item_stabilization(
    timeline_item_id: str, enabled: bool = None, method: str = None, strength: float = None
) -> Dict[str, Any]:
    """Set stabilization properties for a timeline item.

    Args:
        timeline_item_id: The ID of the timeline item to modify
        enabled: Optional boolean to enable/disable stabilization
        method: Optional stabilization method. Options: 'Perspective', 'Similarity', 'Translation'
        strength: Optional strength value (0.0 to 1.0)
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

    # Validate inputs
    if enabled is None and method is None and strength is None:
        return error_response("INVALID_ARG", "Must specify at least one parameter to modify")

    valid_methods = ["Perspective", "Similarity", "Translation"]
    if method and method not in valid_methods:
        return error_response(
            "INVALID_ARG", f"Invalid stabilization method. Must be one of: {', '.join(valid_methods)}"
        )

    if strength is not None and (strength < 0.0 or strength > 1.0):
        return error_response("INVALID_ARG", "Strength must be between 0.0 and 1.0")

    try:
        # Find the timeline item by ID
        video_track_count = current_timeline.GetTrackCount("video")

        timeline_item = None

        # Search video tracks
        for track_index in range(1, video_track_count + 1):
            items = current_timeline.GetItemListInTrack("video", track_index)
            if items:
                for item in items:
                    if str(item.GetUniqueId()) == timeline_item_id:
                        timeline_item = item
                        break
            if timeline_item:
                break

        if not timeline_item:
            return error_response("NOT_FOUND", f"Video timeline item with ID '{timeline_item_id}' not found")

        if timeline_item.GetType() != "Video":
            return error_response("INVALID_ARG", f"Timeline item with ID '{timeline_item_id}' is not a video item")

        op_success = True

        # Set enabled if specified
        if enabled is not None:
            result = timeline_item.SetProperty("StabilizationEnable", 1 if enabled else 0)
            if not result:
                op_success = False

        # Set method if specified
        if method:
            result = timeline_item.SetProperty("StabilizationMethod", method)
            if not result:
                op_success = False

        # Set strength if specified
        if strength is not None:
            result = timeline_item.SetProperty("StabilizationStrength", strength)
            if not result:
                op_success = False

        if op_success:
            changes = []
            if enabled is not None:
                changes.append(f"stabilization {'enabled' if enabled else 'disabled'}")
            if method:
                changes.append(f"stabilization method to '{method}'")
            if strength is not None:
                changes.append(f"stabilization strength to {strength}")

            return success_response(
                message=f"Set {' and '.join(changes)} for timeline item '{timeline_item.GetName()}'",
                context={
                    "timeline_item_id": timeline_item_id,
                    "enabled": enabled,
                    "method": method,
                    "strength": strength,
                },
            )
        else:
            return error_response(
                "OPERATION_FAILED",
                f"Failed to set some stabilization properties for timeline item '{timeline_item.GetName()}'",
            )
    except Exception as e:
        return error_response("OPERATION_FAILED", f"Error setting timeline item stabilization properties: {str(e)}")


@tool()
def set_timeline_item_audio(
    timeline_item_id: str, volume: float = None, pan: float = None, eq_enabled: bool = None
) -> Dict[str, Any]:
    """Set audio properties for a timeline item.

    Args:
        timeline_item_id: The ID of the timeline item to modify
        volume: Optional volume level (usually 0.0 to 2.0, where 1.0 is unity gain)
        pan: Optional pan value (-1.0 to 1.0, where -1.0 is left, 0 is center, 1.0 is right)
        eq_enabled: Optional boolean to enable/disable EQ
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

    # Validate inputs
    if volume is None and pan is None and eq_enabled is None:
        return error_response("INVALID_ARG", "Must specify at least one parameter to modify")

    if volume is not None and volume < 0.0:
        return error_response("INVALID_ARG", "Volume must be greater than or equal to 0.0")

    if pan is not None and (pan < -1.0 or pan > 1.0):
        return error_response("INVALID_ARG", "Pan must be between -1.0 and 1.0")

    try:
        # Find the timeline item by ID
        video_track_count = current_timeline.GetTrackCount("video")
        audio_track_count = current_timeline.GetTrackCount("audio")

        timeline_item = None
        is_audio = False

        # Search audio tracks first
        for track_index in range(1, audio_track_count + 1):
            items = current_timeline.GetItemListInTrack("audio", track_index)
            if items:
                for item in items:
                    if str(item.GetUniqueId()) == timeline_item_id:
                        timeline_item = item
                        is_audio = True
                        break
            if timeline_item:
                break

        # If not found in audio tracks, search video tracks (might be a video clip with audio)
        if not timeline_item:
            for track_index in range(1, video_track_count + 1):
                items = current_timeline.GetItemListInTrack("video", track_index)
                if items:
                    for item in items:
                        if str(item.GetUniqueId()) == timeline_item_id:
                            timeline_item = item
                            break
                if timeline_item:
                    break

        if not timeline_item:
            return error_response("NOT_FOUND", f"Timeline item with ID '{timeline_item_id}' not found")

        # Check if the item has audio capabilities
        if not is_audio and timeline_item.GetMediaType() != "Audio":
            return error_response(
                "INVALID_ARG", f"Timeline item with ID '{timeline_item_id}' does not have audio properties"
            )

        op_success = True

        # Set volume if specified
        if volume is not None:
            result = timeline_item.SetProperty("Volume", volume)
            if not result:
                op_success = False

        # Set pan if specified
        if pan is not None:
            result = timeline_item.SetProperty("Pan", pan)
            if not result:
                op_success = False

        # Set EQ enabled if specified
        if eq_enabled is not None:
            result = timeline_item.SetProperty("EQEnable", 1 if eq_enabled else 0)
            if not result:
                op_success = False

        if op_success:
            changes = []
            if volume is not None:
                changes.append(f"volume to {volume}")
            if pan is not None:
                changes.append(f"pan to {pan}")
            if eq_enabled is not None:
                changes.append(f"EQ {'enabled' if eq_enabled else 'disabled'}")

            return success_response(
                message=f"Set {' and '.join(changes)} for timeline item '{timeline_item.GetName()}'",
                context={"timeline_item_id": timeline_item_id, "volume": volume, "pan": pan, "eq_enabled": eq_enabled},
            )
        else:
            return error_response(
                "OPERATION_FAILED", f"Failed to set some audio properties for timeline item '{timeline_item.GetName()}'"
            )
    except Exception as e:
        return error_response("OPERATION_FAILED", f"Error setting timeline item audio properties: {str(e)}")


@tool()
def set_timeline_item_name(timeline_item_id: str, name: str) -> Dict[str, Any]:
    """Set the name of a timeline item.

    Args:
        timeline_item_id: The ID of the timeline item
        name: The new name
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

    try:
        # Find item
        video_track_count = current_timeline.GetTrackCount("video")
        timeline_item = None

        for track_index in range(1, video_track_count + 1):
            items = current_timeline.GetItemListInTrack("video", track_index)
            if items:
                for item in items:
                    if str(item.GetUniqueId()) == timeline_item_id:
                        timeline_item = item
                        break
            if timeline_item:
                break

        if not timeline_item:
            return error_response("NOT_FOUND", f"Timeline item {timeline_item_id} not found")

        if timeline_item.SetName(name):
            return success_response(
                message=f"Set name to '{name}'",
                context={"timeline_item_id": timeline_item_id, "name": name},
            )
        else:
            return error_response("OPERATION_FAILED", f"Failed to set name for item {timeline_item_id}")

    except Exception as e:
        return error_response("OPERATION_FAILED", f"Error setting name: {str(e)}")


@resource("resolve://timeline-items-list")
def get_timeline_items_resource() -> List[Dict[str, Any]]:
    """Get all items in the current timeline with their IDs and basic properties."""
    if resolve is None:
        return [{"error": "Not connected to DaVinci Resolve"}]

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return [{"error": "Failed to get Project Manager"}]

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return [{"error": "No project currently open"}]

    current_timeline = current_project.GetCurrentTimeline()
    if not current_timeline:
        return [{"error": "No timeline currently active"}]

    try:
        video_track_count = current_timeline.GetTrackCount("video")
        audio_track_count = current_timeline.GetTrackCount("audio")

        items = []

        for track_index in range(1, video_track_count + 1):
            track_items = current_timeline.GetItemListInTrack("video", track_index)
            if track_items:
                for item in track_items:
                    items.append(
                        {
                            "id": str(item.GetUniqueId()),
                            "name": item.GetName(),
                            "type": "video",
                            "track": track_index,
                            "start_frame": item.GetStart(),
                            "end_frame": item.GetEnd(),
                            "duration": item.GetDuration(),
                        }
                    )

        for track_index in range(1, audio_track_count + 1):
            track_items = current_timeline.GetItemListInTrack("audio", track_index)
            if track_items:
                for item in track_items:
                    items.append(
                        {
                            "id": str(item.GetUniqueId()),
                            "name": item.GetName(),
                            "type": "audio",
                            "track": track_index,
                            "start_frame": item.GetStart(),
                            "end_frame": item.GetEnd(),
                            "duration": item.GetDuration(),
                        }
                    )

        if not items:
            return [{"info": "No items found in the current timeline"}]

        return items
    except Exception as e:
        return [{"error": f"Error listing timeline items: {str(e)}"}]


def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
