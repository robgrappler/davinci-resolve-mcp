"""Handlers for media pool browsing and manipulation handlers."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers
from davinci_resolve_mcp.utils.response import success_response, error_response

from davinci_resolve_mcp.handlers.timelines import list_timelines

logger = logging.getLogger("davinci-resolve-mcp.media_pool")
registry = HandlerRegistry()
resource = registry.resource
tool = registry.tool
resolve: Optional[Any] = None


@resource("resolve://media-pool-clips")
def list_media_pool_clips() -> List[Dict[str, Any]]:
    """List all clips in the root folder of the media pool."""
    if resolve is None:
        return [{"error": "Not connected to DaVinci Resolve"}]

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return [{"error": "Failed to get Project Manager"}]

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return [{"error": "No project currently open"}]

    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return [{"error": "Failed to get Media Pool"}]

    root_folder = media_pool.GetRootFolder()
    if not root_folder:
        return [{"error": "Failed to get root folder"}]

    clips = root_folder.GetClipList()
    if not clips:
        return [{"info": "No clips found in the root folder"}]

    # Return a simplified list with basic clip info
    result = []
    for clip in clips:
        result.append({"name": clip.GetName(), "duration": clip.GetDuration(), "fps": clip.GetClipProperty("FPS")})

    return result


@tool()
def import_media(file_path: str) -> Dict[str, Any]:
    """Import media file into the current project's media pool.

    Args:
        file_path: The path to the media file to import
    """
    from davinci_resolve_mcp.api.media_operations import import_media as import_media_func

    result = import_media_func(resolve, file_path)
    if isinstance(result, str):
        if result.startswith("Error:"):
            return error_response("OPERATION_FAILED", result[7:].strip())
        elif result.startswith("Failed"):
            return error_response("OPERATION_FAILED", result)
        else:
            return success_response(message=result, context={"file_path": file_path})
    return success_response(data=result, context={"file_path": file_path})


@tool()
def delete_media(clip_name: str) -> Dict[str, Any]:
    """Delete a media clip from the media pool by name.

    Args:
        clip_name: Name of the clip to delete
    """
    from davinci_resolve_mcp.api.media_operations import delete_media as delete_media_func

    result = delete_media_func(resolve, clip_name)
    if isinstance(result, str):
        if result.startswith("Error:"):
            return error_response("OPERATION_FAILED", result[7:].strip())
        elif result.startswith("Failed"):
            return error_response("OPERATION_FAILED", result)
        else:
            return success_response(message=result, context={"clip_name": clip_name})
    return success_response(data=result, context={"clip_name": clip_name})


@tool()
def move_media_to_bin(clip_name: str, bin_name: str) -> Dict[str, Any]:
    """Move a media clip to a specific bin in the media pool.

    Args:
        clip_name: Name of the clip to move
        bin_name: Name of the target bin
    """
    from davinci_resolve_mcp.api.media_operations import move_media_to_bin as move_media_func

    result = move_media_func(resolve, clip_name, bin_name)
    if isinstance(result, str):
        if result.startswith("Error:"):
            return error_response("OPERATION_FAILED", result[7:].strip())
        elif result.startswith("Failed"):
            return error_response("OPERATION_FAILED", result)
        else:
            return success_response(message=result, context={"clip_name": clip_name, "bin_name": bin_name})
    return success_response(data=result, context={"clip_name": clip_name, "bin_name": bin_name})


@tool()
def auto_sync_audio(
    clip_names: List[str], sync_method: str = "waveform", append_mode: bool = False, target_bin: str = None
) -> Dict[str, Any]:
    """Sync audio between clips with customizable settings.

    Args:
        clip_names: List of clip names to sync
        sync_method: Method to use for synchronization - 'waveform' or 'timecode'
        append_mode: Whether to append the audio or replace it
        target_bin: Optional bin to move synchronized clips to
    """
    from davinci_resolve_mcp.api.media_operations import auto_sync_audio as auto_sync_audio_func

    result = auto_sync_audio_func(resolve, clip_names, sync_method, append_mode, target_bin)
    if isinstance(result, str):
        if result.startswith("Error:"):
            return error_response("OPERATION_FAILED", result[7:].strip())
        elif result.startswith("Failed"):
            return error_response("OPERATION_FAILED", result)
        else:
            return success_response(message=result, context={"clip_names": clip_names, "sync_method": sync_method})
    return success_response(data=result, context={"clip_names": clip_names, "sync_method": sync_method})


@tool()
def unlink_clips(clip_names: List[str]) -> Dict[str, Any]:
    """Unlink specified clips, disconnecting them from their media files.

    Args:
        clip_names: List of clip names to unlink
    """
    from davinci_resolve_mcp.api.media_operations import unlink_clips as unlink_clips_func

    result = unlink_clips_func(resolve, clip_names)
    if isinstance(result, str):
        if result.startswith("Error:"):
            return error_response("OPERATION_FAILED", result[7:].strip())
        elif result.startswith("Failed"):
            return error_response("OPERATION_FAILED", result)
        else:
            return success_response(message=result, context={"clip_names": clip_names})
    return success_response(data=result, context={"clip_names": clip_names})


@tool()
def relink_clips(
    clip_names: List[str], media_paths: List[str] = None, folder_path: str = None, recursive: bool = False
) -> Dict[str, Any]:
    """Relink specified clips to their media files.

    Args:
        clip_names: List of clip names to relink
        media_paths: Optional list of specific media file paths to use for relinking
        folder_path: Optional folder path to search for media files
        recursive: Whether to search the folder path recursively
    """
    from davinci_resolve_mcp.api.media_operations import relink_clips as relink_clips_func

    result = relink_clips_func(resolve, clip_names, media_paths, folder_path, recursive)
    if isinstance(result, str):
        if result.startswith("Error:"):
            return error_response("OPERATION_FAILED", result[7:].strip())
        elif result.startswith("Failed"):
            return error_response("OPERATION_FAILED", result)
        else:
            return success_response(message=result, context={"clip_names": clip_names})
    return success_response(data=result, context={"clip_names": clip_names})


@tool()
def create_sub_clip(
    clip_name: str, start_frame: int, end_frame: int, sub_clip_name: str = None, bin_name: str = None
) -> Dict[str, Any]:
    """Create a subclip from the specified clip using in and out points.

    Args:
        clip_name: Name of the source clip
        start_frame: Start frame (in point)
        end_frame: End frame (out point)
        sub_clip_name: Optional name for the subclip (defaults to original name with '_subclip')
        bin_name: Optional bin to place the subclip in
    """
    from davinci_resolve_mcp.api.media_operations import create_sub_clip as create_sub_clip_func

    result = create_sub_clip_func(resolve, clip_name, start_frame, end_frame, sub_clip_name, bin_name)
    if isinstance(result, str):
        if result.startswith("Error:"):
            return error_response("OPERATION_FAILED", result[7:].strip())
        elif result.startswith("Failed"):
            return error_response("OPERATION_FAILED", result)
        else:
            return success_response(
                message=result, context={"clip_name": clip_name, "start_frame": start_frame, "end_frame": end_frame}
            )
    return success_response(
        data=result, context={"clip_name": clip_name, "start_frame": start_frame, "end_frame": end_frame}
    )


@tool()
def create_bin(name: str) -> Dict[str, Any]:
    """Create a new bin/folder in the media pool.

    Args:
        name: The name for the new bin
    """
    from davinci_resolve_mcp.api.media_operations import create_bin as create_bin_func

    result = create_bin_func(resolve, name)
    if isinstance(result, str):
        if result.startswith("Error:"):
            return error_response("OPERATION_FAILED", result[7:].strip())
        elif result.startswith("Failed"):
            return error_response("OPERATION_FAILED", result)
        else:
            return success_response(message=result, context={"bin_name": name})
    return success_response(data=result, context={"bin_name": name})


@resource("resolve://media-pool-bins")
def list_media_pool_bins() -> List[Dict[str, Any]]:
    """List all bins/folders in the media pool."""
    from davinci_resolve_mcp.api.media_operations import list_bins as list_bins_func

    return list_bins_func(resolve)


@resource("resolve://media-pool-bin/{bin_name}")
def get_media_pool_bin_contents(bin_name: str) -> List[Dict[str, Any]]:
    """Get contents of a specific bin/folder in the media pool.

    Args:
        bin_name: The name of the bin to get contents from. Use 'Master' for the root folder.
    """
    from davinci_resolve_mcp.api.media_operations import get_bin_contents as get_bin_contents_func

    return get_bin_contents_func(resolve, bin_name)


@resource("resolve://timeline-clips")
def list_timeline_clips() -> List[Dict[str, Any]]:
    """List all clips in the current timeline."""
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
        # Video tracks are 1-based index (1 is first track)
        video_track_count = current_timeline.GetTrackCount("video")
        audio_track_count = current_timeline.GetTrackCount("audio")

        clips = []

        # Process video tracks
        for track_index in range(1, video_track_count + 1):
            track_items = current_timeline.GetItemListInTrack("video", track_index)
            if track_items:
                for item in track_items:
                    clips.append(
                        {
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
                    clips.append(
                        {
                            "name": item.GetName(),
                            "type": "audio",
                            "track": track_index,
                            "start_frame": item.GetStart(),
                            "end_frame": item.GetEnd(),
                            "duration": item.GetDuration(),
                        }
                    )

        if not clips:
            return [{"info": "No clips found in the current timeline"}]

        return clips
    except Exception as e:
        return [{"error": f"Error listing timeline clips: {str(e)}"}]


@tool()
def list_timelines_tool() -> Dict[str, Any]:
    """List all timelines in the current project as a tool."""
    logger.info("Received request to list timelines via tool")
    result = list_timelines()
    if isinstance(result, list) and len(result) > 0 and isinstance(result[0], str) and result[0].startswith("Error"):
        return error_response(
            "OPERATION_FAILED", result[0][7:].strip() if result[0].startswith("Error: ") else result[0]
        )
    return success_response(data=result, message=f"Found {len(result)} timelines" if isinstance(result, list) else None)


@tool()
def add_clip_to_timeline(clip_name: str, timeline_name: str = None) -> Dict[str, Any]:
    """Add a media pool clip to the timeline.

    Args:
        clip_name: Name of the clip in the media pool
        timeline_name: Optional timeline to target (uses current if not specified)
    """
    from davinci_resolve_mcp.api.media_operations import add_clip_to_timeline as add_clip_func

    result = add_clip_func(resolve, clip_name, timeline_name)
    if isinstance(result, str):
        if result.startswith("Error:"):
            return error_response("OPERATION_FAILED", result[7:].strip())
        elif result.startswith("Failed"):
            return error_response("OPERATION_FAILED", result)
        else:
            return success_response(message=result, context={"clip_name": clip_name, "timeline_name": timeline_name})
    return success_response(data=result, context={"clip_name": clip_name, "timeline_name": timeline_name})


@tool()
def create_timeline_from_clips(timeline_name: str, clip_names: List[str]) -> Dict[str, Any]:
    """Create a new timeline containing the specified list of clips.

    Args:
        timeline_name: Name for the new timeline
        clip_names: List of clip names to include in order
    """
    from davinci_resolve_mcp.api.media_operations import create_timeline_from_clips as create_func

    result = create_func(resolve, timeline_name, clip_names)
    if isinstance(result, str):
        if result.startswith("Error:"):
            return error_response("OPERATION_FAILED", result[7:].strip())
        elif result.startswith("Failed"):
            return error_response("OPERATION_FAILED", result)
        else:
            return success_response(
                message=result, context={"timeline_name": timeline_name, "clip_count": len(clip_names)}
            )
    return success_response(data=result, context={"timeline_name": timeline_name, "clip_count": len(clip_names)})


@tool()
def list_media_pool_items() -> Dict[str, Any]:
    """List all items in the media pool (recursive)."""
    if resolve is None:
        return error_response("NOT_CONNECTED", "Not connected to DaVinci Resolve")

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return error_response("OPERATION_FAILED", "Failed to get Media Pool")

    from davinci_resolve_mcp.handlers.delivery import get_all_media_pool_clips

    clips = get_all_media_pool_clips(media_pool)
    items = []
    for c in clips:
        name = c.GetName()
        file_path = c.GetClipProperty("File Path")
        items.append({"name": name, "file_path": file_path})

    return success_response(data=items, message=f"Found {len(items)} media pool items")


def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
