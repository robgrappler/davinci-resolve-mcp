"""Handlers for delivery/render queue handlers."""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional, Union
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers

logger = logging.getLogger("davinci-resolve-mcp.delivery")
registry = HandlerRegistry()
resource = registry.resource
tool = registry.tool
resolve: Optional[Any] = None

@resource("resolve://delivery/render-presets")
def get_render_presets() -> List[Dict[str, Any]]:
    """Get all available render presets in the current project."""
    from api.delivery_operations import get_render_presets as get_presets_func
    return get_presets_func(resolve)

@tool()
def add_to_render_queue(preset_name: str, timeline_name: str = None, use_in_out_range: bool = False) -> Dict[str, Any]:
    """Add a timeline to the render queue with the specified preset.
    
    Args:
        preset_name: Name of the render preset to use
        timeline_name: Name of the timeline to render (uses current if None)
        use_in_out_range: Whether to render only the in/out range instead of entire timeline
    """
    from api.delivery_operations import add_to_render_queue as add_queue_func
    return add_queue_func(resolve, preset_name, timeline_name, use_in_out_range)

@tool()
def start_render() -> Dict[str, Any]:
    """Start rendering the jobs in the render queue."""
    from api.delivery_operations import start_render as start_render_func
    return start_render_func(resolve)

@resource("resolve://delivery/render-queue/status")
def get_render_queue_status() -> Dict[str, Any]:
    """Get the status of jobs in the render queue."""
    from api.delivery_operations import get_render_queue_status as get_status_func
    return get_status_func(resolve)

@tool()
def clear_render_queue() -> Dict[str, Any]:
    """Clear all jobs from the render queue."""
    from api.delivery_operations import clear_render_queue as clear_queue_func
    return clear_queue_func(resolve)

@tool()
def link_proxy_media(clip_name: str, proxy_file_path: str) -> str:
    """Link a proxy media file to a clip.
    
    Args:
        clip_name: Name of the clip to link proxy to
        proxy_file_path: Path to the proxy media file
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the clip by name
    clips = get_all_media_pool_clips(media_pool)
    target_clip = None
    
    for clip in clips:
        if clip.GetName() == clip_name:
            target_clip = clip
            break
    
    if not target_clip:
        return f"Error: Clip '{clip_name}' not found in Media Pool"
    
    # Check if file exists
    if not os.path.exists(proxy_file_path):
        return f"Error: Proxy file '{proxy_file_path}' does not exist"
    
    try:
        result = target_clip.LinkProxyMedia(proxy_file_path)
        if result:
            return f"Successfully linked proxy media '{proxy_file_path}' to clip '{clip_name}'"
        else:
            return f"Failed to link proxy media to clip '{clip_name}'"
    except Exception as e:
        return f"Error linking proxy media: {str(e)}"

@tool()
def unlink_proxy_media(clip_name: str) -> str:
    """Unlink proxy media from a clip.
    
    Args:
        clip_name: Name of the clip to unlink proxy from
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the clip by name
    clips = get_all_media_pool_clips(media_pool)
    target_clip = None
    
    for clip in clips:
        if clip.GetName() == clip_name:
            target_clip = clip
            break
    
    if not target_clip:
        return f"Error: Clip '{clip_name}' not found in Media Pool"
    
    try:
        result = target_clip.UnlinkProxyMedia()
        if result:
            return f"Successfully unlinked proxy media from clip '{clip_name}'"
        else:
            return f"Failed to unlink proxy media from clip '{clip_name}'"
    except Exception as e:
        return f"Error unlinking proxy media: {str(e)}"

@tool()
def replace_clip(clip_name: str, replacement_path: str) -> str:
    """Replace a clip with another media file.
    
    Args:
        clip_name: Name of the clip to be replaced
        replacement_path: Path to the replacement media file
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the clip by name
    clips = get_all_media_pool_clips(media_pool)
    target_clip = None
    
    for clip in clips:
        if clip.GetName() == clip_name:
            target_clip = clip
            break
    
    if not target_clip:
        return f"Error: Clip '{clip_name}' not found in Media Pool"
    
    # Check if file exists
    if not os.path.exists(replacement_path):
        return f"Error: Replacement file '{replacement_path}' does not exist"
    
    try:
        result = target_clip.ReplaceClip(replacement_path)
        if result:
            return f"Successfully replaced clip '{clip_name}' with '{replacement_path}'"
        else:
            return f"Failed to replace clip '{clip_name}'"
    except Exception as e:
        return f"Error replacing clip: {str(e)}"

@tool()
def transcribe_audio(clip_name: str, language: str = "en-US") -> str:
    """Transcribe audio for a clip.
    
    Args:
        clip_name: Name of the clip to transcribe
        language: Language code for transcription (default: en-US)
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the clip by name
    clips = get_all_media_pool_clips(media_pool)
    target_clip = None
    
    for clip in clips:
        if clip.GetName() == clip_name:
            target_clip = clip
            break
    
    if not target_clip:
        return f"Error: Clip '{clip_name}' not found in Media Pool"
    
    try:
        result = target_clip.TranscribeAudio(language)
        if result:
            return f"Successfully started audio transcription for clip '{clip_name}' in language '{language}'"
        else:
            return f"Failed to start audio transcription for clip '{clip_name}'"
    except Exception as e:
        return f"Error during audio transcription: {str(e)}"

@tool()
def clear_transcription(clip_name: str) -> str:
    """Clear audio transcription for a clip.
    
    Args:
        clip_name: Name of the clip to clear transcription from
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the clip by name
    clips = get_all_media_pool_clips(media_pool)
    target_clip = None
    
    for clip in clips:
        if clip.GetName() == clip_name:
            target_clip = clip
            break
    
    if not target_clip:
        return f"Error: Clip '{clip_name}' not found in Media Pool"
    
    try:
        result = target_clip.ClearTranscription()
        if result:
            return f"Successfully cleared audio transcription for clip '{clip_name}'"
        else:
            return f"Failed to clear audio transcription for clip '{clip_name}'"
    except Exception as e:
        return f"Error clearing audio transcription: {str(e)}"

# Utility function to get all clips from the media pool (recursively)
def get_all_media_pool_clips(media_pool):
    """Get all clips from media pool recursively including subfolders."""
    clips = []
    root_folder = media_pool.GetRootFolder()
    
    def process_folder(folder):
        folder_clips = folder.GetClipList()
        if folder_clips:
            clips.extend(folder_clips)
        
        sub_folders = folder.GetSubFolderList()
        for sub_folder in sub_folders:
            process_folder(sub_folder)
    
    process_folder(root_folder)
    return clips

@tool()
def export_folder(folder_name: str, export_path: str, export_type: str = "DRB") -> str:
    """Export a folder to a DRB file or other format.
    
    Args:
        folder_name: Name of the folder to export
        export_path: Path to save the exported file
        export_type: Export format (DRB is default and currently the only supported option)
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the folder by name
    target_folder = None
    root_folder = media_pool.GetRootFolder()
    
    if folder_name.lower() == "root" or folder_name.lower() == "master":
        target_folder = root_folder
    else:
        # Search for the folder by name
        folders = get_all_media_pool_folders(media_pool)
        for folder in folders:
            if folder.GetName() == folder_name:
                target_folder = folder
                break
    
    if not target_folder:
        return f"Error: Folder '{folder_name}' not found in Media Pool"
    
    # Check if directory exists, create if not
    export_dir = os.path.dirname(export_path)
    if not os.path.exists(export_dir) and export_dir:
        try:
            os.makedirs(export_dir)
        except Exception as e:
            return f"Error creating directory for export: {str(e)}"
    
    # Export the folder
    try:
        result = target_folder.Export(export_path)
        if result:
            return f"Successfully exported folder '{folder_name}' to '{export_path}'"
        else:
            return f"Failed to export folder '{folder_name}'"
    except Exception as e:
        return f"Error exporting folder: {str(e)}"

@tool()
def transcribe_folder_audio(folder_name: str, language: str = "en-US") -> str:
    """Transcribe audio for all clips in a folder.
    
    Args:
        folder_name: Name of the folder containing clips to transcribe
        language: Language code for transcription (default: en-US)
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the folder by name
    target_folder = None
    root_folder = media_pool.GetRootFolder()
    
    if folder_name.lower() == "root" or folder_name.lower() == "master":
        target_folder = root_folder
    else:
        # Search for the folder by name
        folders = get_all_media_pool_folders(media_pool)
        for folder in folders:
            if folder.GetName() == folder_name:
                target_folder = folder
                break
    
    if not target_folder:
        return f"Error: Folder '{folder_name}' not found in Media Pool"
    
    # Transcribe audio in the folder
    try:
        result = target_folder.TranscribeAudio(language)
        if result:
            return f"Successfully started audio transcription for folder '{folder_name}' in language '{language}'"
        else:
            return f"Failed to start audio transcription for folder '{folder_name}'"
    except Exception as e:
        return f"Error during audio transcription: {str(e)}"

@tool()
def clear_folder_transcription(folder_name: str) -> str:
    """Clear audio transcription for all clips in a folder.
    
    Args:
        folder_name: Name of the folder to clear transcriptions from
    """
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    
    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return "Error: Failed to get Project Manager"
    
    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return "Error: No project currently open"
    
    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return "Error: Failed to get Media Pool"
    
    # Find the folder by name
    target_folder = None
    root_folder = media_pool.GetRootFolder()
    
    if folder_name.lower() == "root" or folder_name.lower() == "master":
        target_folder = root_folder
    else:
        # Search for the folder by name
        folders = get_all_media_pool_folders(media_pool)
        for folder in folders:
            if folder.GetName() == folder_name:
                target_folder = folder
                break
    
    if not target_folder:
        return f"Error: Folder '{folder_name}' not found in Media Pool"
    
    # Clear transcription for the folder
    try:
        result = target_folder.ClearTranscription()
        if result:
            return f"Successfully cleared audio transcription for folder '{folder_name}'"
        else:
            return f"Failed to clear audio transcription for folder '{folder_name}'"
    except Exception as e:
        return f"Error clearing audio transcription: {str(e)}"

# Utility function to get all folders from the media pool (recursively)
def get_all_media_pool_folders(media_pool):
    """Get all folders from media pool recursively."""
    folders = []
    root_folder = media_pool.GetRootFolder()
    
    def process_folder(folder):
        folders.append(folder)
        
        sub_folders = folder.GetSubFolderList()
        for sub_folder in sub_folders:
            process_folder(sub_folder)
    
    process_folder(root_folder)
    return folders

@tool()
def add_to_render_queue_json(
    preset_name: str,
    timeline_name: str = None,
    use_in_out_range: bool = False,
) -> Dict[str, Any]:
    """Pipeline-oriented wrapper around add_to_render_queue.

    Returns a stable ``{"ok": bool, "data": ..., "error": ...}`` object
    regardless of how the underlying helper formats its output.
    """
    from davinci_resolve_mcp.api.delivery_operations import add_to_render_queue as add_queue_func
    from davinci_resolve_mcp.utils.response import success_response, error_response

    logger.info(
        "add_to_render_queue_json: preset=%s timeline=%s in_out=%s",
        preset_name,
        timeline_name,
        use_in_out_range,
    )
    raw = add_queue_func(resolve, preset_name, timeline_name, use_in_out_range)
    context = {"preset_name": preset_name, "timeline_name": timeline_name}

    if isinstance(raw, dict) and "ok" in raw and "error" in raw:
        return raw
    if isinstance(raw, str):
        text = raw.strip()
        if text.startswith("Error:"):
            return error_response(
                code="ADD_TO_RENDER_QUEUE_ERROR",
                message=text[len("Error:"):].strip() or text,
                details={"raw": raw},
                context=context,
            )
        if text.lower().startswith("failed"):
            return error_response(
                code="ADD_TO_RENDER_QUEUE_FAILED",
                message=text,
                details={"raw": raw},
                context=context,
            )
        return success_response(data={"raw": raw}, message=text, context=context)
    if isinstance(raw, dict) and "error" in raw and not raw.get("ok", True):
        err = raw["error"]
        if isinstance(err, dict):
            return error_response(
                code=err.get("code", "ADD_TO_RENDER_QUEUE_ERROR"),
                message=err.get("message", str(err)),
                details=err.get("details", raw),
                context=context,
            )
        return error_response(
            code="ADD_TO_RENDER_QUEUE_ERROR",
            message=str(err),
            details=raw,
            context=context,
        )
    return success_response(data=raw, context=context)

def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
