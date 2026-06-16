"""Handlers for media pool browsing and manipulation handlers."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers

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
def import_media(file_path: str) -> str:
    """Import media file into the current project's media pool.

    Args:
        file_path: The path to the media file to import
    """
    from davinci_resolve_mcp.api.media_operations import import_media as import_media_func

    return import_media_func(resolve, file_path)


@tool()
def delete_media(clip_name: str) -> str:
    """Delete a media clip from the media pool by name.

    Args:
        clip_name: Name of the clip to delete
    """
    from davinci_resolve_mcp.api.media_operations import delete_media as delete_media_func

    return delete_media_func(resolve, clip_name)


@tool()
def move_media_to_bin(clip_name: str, bin_name: str) -> str:
    """Move a media clip to a specific bin in the media pool.

    Args:
        clip_name: Name of the clip to move
        bin_name: Name of the target bin
    """
    from davinci_resolve_mcp.api.media_operations import move_media_to_bin as move_media_func

    return move_media_func(resolve, clip_name, bin_name)


@tool()
def auto_sync_audio(
    clip_names: List[str], sync_method: str = "waveform", append_mode: bool = False, target_bin: str = None
) -> str:
    """Sync audio between clips with customizable settings.

    Args:
        clip_names: List of clip names to sync
        sync_method: Method to use for synchronization - 'waveform' or 'timecode'
        append_mode: Whether to append the audio or replace it
        target_bin: Optional bin to move synchronized clips to
    """
    from davinci_resolve_mcp.api.media_operations import auto_sync_audio as auto_sync_audio_func

    return auto_sync_audio_func(resolve, clip_names, sync_method, append_mode, target_bin)


@tool()
def unlink_clips(clip_names: List[str]) -> str:
    """Unlink specified clips, disconnecting them from their media files.

    Args:
        clip_names: List of clip names to unlink
    """
    from davinci_resolve_mcp.api.media_operations import unlink_clips as unlink_clips_func

    return unlink_clips_func(resolve, clip_names)


@tool()
def relink_clips(
    clip_names: List[str], media_paths: List[str] = None, folder_path: str = None, recursive: bool = False
) -> str:
    """Relink specified clips to their media files.

    Args:
        clip_names: List of clip names to relink
        media_paths: Optional list of specific media file paths to use for relinking
        folder_path: Optional folder path to search for media files
        recursive: Whether to search the folder path recursively
    """
    from davinci_resolve_mcp.api.media_operations import relink_clips as relink_clips_func

    return relink_clips_func(resolve, clip_names, media_paths, folder_path, recursive)


@tool()
def create_sub_clip(
    clip_name: str, start_frame: int, end_frame: int, sub_clip_name: str = None, bin_name: str = None
) -> str:
    """Create a subclip from the specified clip using in and out points.

    Args:
        clip_name: Name of the source clip
        start_frame: Start frame (in point)
        end_frame: End frame (out point)
        sub_clip_name: Optional name for the subclip (defaults to original name with '_subclip')
        bin_name: Optional bin to place the subclip in
    """
    from davinci_resolve_mcp.api.media_operations import create_sub_clip as create_sub_clip_func

    return create_sub_clip_func(resolve, clip_name, start_frame, end_frame, sub_clip_name, bin_name)


@tool()
def create_bin(name: str) -> str:
    """Create a new bin/folder in the media pool.

    Args:
        name: The name for the new bin
    """
    from davinci_resolve_mcp.api.media_operations import create_bin as create_bin_func

    return create_bin_func(resolve, name)


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
def list_timelines_tool() -> List[str]:
    """List all timelines in the current project as a tool."""
    logger.info("Received request to list timelines via tool")
    return list_timelines()


@tool()
def add_clip_to_timeline(
    clip_name: str, timeline_name: str = None, start_frame: int = None, end_frame: int = None
) -> str:
    """Add a media pool clip to the timeline.

    Args:
        clip_name: Name of the clip in the media pool
        timeline_name: Optional timeline to target (uses current if not specified)
        start_frame: Optional start frame (in point) to use from the source clip
        end_frame: Optional end frame (out point) to use from the source clip
    """
    from davinci_resolve_mcp.api.media_operations import add_clip_to_timeline as add_clip_func

    return add_clip_func(resolve, clip_name, timeline_name, start_frame, end_frame)


@tool()
def create_timeline_from_clips(timeline_name: str, clip_names: List[str]) -> str:
    """Create a new timeline containing the specified list of clips.

    Args:
        timeline_name: Name for the new timeline
        clip_names: List of clip names to include in order
    """
    from davinci_resolve_mcp.api.media_operations import create_timeline_from_clips as create_func

    return create_func(resolve, timeline_name, clip_names)


@tool()
def list_media_pool_items() -> str:
    """List all items in the media pool (recursive)."""
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"

    project_manager = resolve.GetProjectManager()
    current_project = project_manager.GetCurrentProject()
    media_pool = current_project.GetMediaPool()

    from davinci_resolve_mcp.handlers.delivery import get_all_media_pool_clips

    clips = get_all_media_pool_clips(media_pool)
    result = []
    for c in clips:
        name = c.GetName()
        file_path = c.GetClipProperty("File Path")
        result.append(f"Name: {name}, File Path: {file_path}")

    return "\n".join(result)


def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
