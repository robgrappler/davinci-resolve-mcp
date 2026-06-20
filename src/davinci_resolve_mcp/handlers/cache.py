"""Handlers for cache and optimized media configuration handlers."""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers

from davinci_resolve_mcp.handlers.delivery import get_all_media_pool_clips
from davinci_resolve_mcp.utils.response import success_response, error_response

logger = logging.getLogger("davinci-resolve-mcp.cache")
registry = HandlerRegistry()
resource = registry.resource
tool = registry.tool
resolve: Optional[Any] = None


@resource("resolve://cache/settings")
def get_cache_settings() -> Dict[str, Any]:
    """Get current cache settings from the project."""
    if resolve is None:
        return {"error": "Not connected to DaVinci Resolve"}

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return {"error": "Failed to get Project Manager"}

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return {"error": "No project currently open"}

    try:
        # Get all cache-related settings
        settings = {}
        cache_keys = [
            "CacheMode",
            "CacheClipMode",
            "OptimizedMediaMode",
            "ProxyMode",
            "ProxyQuality",
            "TimelineCacheMode",
            "LocalCachePath",
            "NetworkCachePath",
        ]

        for key in cache_keys:
            value = current_project.GetSetting(key)
            settings[key] = value

        return settings
    except Exception as e:
        return {"error": f"Failed to get cache settings: {str(e)}"}


@tool()
def set_cache_mode(mode: str) -> Dict[str, Any]:
    """Set cache mode for the current project.

    Args:
        mode: Cache mode to set. Options: 'auto', 'on', 'off'
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("NO_PROJECT", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    # Validate mode
    valid_modes = ["auto", "on", "off"]
    mode = mode.lower()
    if mode not in valid_modes:
        return error_response(
            "INVALID_ARG",
            f"Invalid cache mode. Must be one of: {', '.join(valid_modes)}",
            context={"mode": mode, "valid_modes": valid_modes},
        )

    # Convert mode to API value
    mode_map = {"auto": "0", "on": "1", "off": "2"}

    try:
        result = current_project.SetSetting("CacheMode", mode_map[mode])
        if result:
            return success_response({"mode": mode}, message=f"Successfully set cache mode to '{mode}'")
        else:
            return error_response("OPERATION_FAILED", f"Failed to set cache mode to '{mode}'", context={"mode": mode})
    except Exception as e:
        return error_response("OPERATION_FAILED", f"Error setting cache mode: {str(e)}", context={"mode": mode})


@tool()
def set_optimized_media_mode(mode: str) -> Dict[str, Any]:
    """Set optimized media mode for the current project.

    Args:
        mode: Optimized media mode to set. Options: 'auto', 'on', 'off'
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("NO_PROJECT", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    # Validate mode
    valid_modes = ["auto", "on", "off"]
    mode = mode.lower()
    if mode not in valid_modes:
        return error_response(
            "INVALID_ARG",
            f"Invalid optimized media mode. Must be one of: {', '.join(valid_modes)}",
            context={"mode": mode, "valid_modes": valid_modes},
        )

    # Convert mode to API value
    mode_map = {"auto": "0", "on": "1", "off": "2"}

    try:
        result = current_project.SetSetting("OptimizedMediaMode", mode_map[mode])
        if result:
            return success_response({"mode": mode}, message=f"Successfully set optimized media mode to '{mode}'")
        else:
            return error_response(
                "OPERATION_FAILED", f"Failed to set optimized media mode to '{mode}'", context={"mode": mode}
            )
    except Exception as e:
        return error_response(
            "OPERATION_FAILED", f"Error setting optimized media mode: {str(e)}", context={"mode": mode}
        )


@tool()
def set_proxy_mode(mode: str) -> Dict[str, Any]:
    """Set proxy media mode for the current project.

    Args:
        mode: Proxy mode to set. Options: 'auto', 'on', 'off'
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("NO_PROJECT", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    # Validate mode
    valid_modes = ["auto", "on", "off"]
    mode = mode.lower()
    if mode not in valid_modes:
        return error_response(
            "INVALID_ARG",
            f"Invalid proxy mode. Must be one of: {', '.join(valid_modes)}",
            context={"mode": mode, "valid_modes": valid_modes},
        )

    # Convert mode to API value
    mode_map = {"auto": "0", "on": "1", "off": "2"}

    try:
        result = current_project.SetSetting("ProxyMode", mode_map[mode])
        if result:
            return success_response({"mode": mode}, message=f"Successfully set proxy mode to '{mode}'")
        else:
            return error_response("OPERATION_FAILED", f"Failed to set proxy mode to '{mode}'", context={"mode": mode})
    except Exception as e:
        return error_response("OPERATION_FAILED", f"Error setting proxy mode: {str(e)}", context={"mode": mode})


@tool()
def set_proxy_quality(quality: str) -> Dict[str, Any]:
    """Set proxy media quality for the current project.

    Args:
        quality: Proxy quality to set. Options: 'quarter', 'half', 'threeQuarter', 'full'
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("NO_PROJECT", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    # Validate quality
    valid_qualities = ["quarter", "half", "threeQuarter", "full"]
    if quality not in valid_qualities:
        return error_response(
            "INVALID_ARG",
            f"Invalid proxy quality. Must be one of: {', '.join(valid_qualities)}",
            context={"quality": quality, "valid_qualities": valid_qualities},
        )

    # Convert quality to API value
    quality_map = {"quarter": "0", "half": "1", "threeQuarter": "2", "full": "3"}

    try:
        result = current_project.SetSetting("ProxyQuality", quality_map[quality])
        if result:
            return success_response({"quality": quality}, message=f"Successfully set proxy quality to '{quality}'")
        else:
            return error_response(
                "OPERATION_FAILED", f"Failed to set proxy quality to '{quality}'", context={"quality": quality}
            )
    except Exception as e:
        return error_response(
            "OPERATION_FAILED", f"Error setting proxy quality: {str(e)}", context={"quality": quality}
        )


@tool()
def set_cache_path(path_type: str, path: str) -> Dict[str, Any]:
    """Set cache file path for the current project.

    Args:
        path_type: Type of cache path to set. Options: 'local', 'network'
        path: File system path for the cache
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("NO_PROJECT", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    # Validate path_type
    valid_path_types = ["local", "network"]
    path_type = path_type.lower()
    if path_type not in valid_path_types:
        return error_response(
            "INVALID_ARG",
            f"Invalid path type. Must be one of: {', '.join(valid_path_types)}",
            context={"path_type": path_type, "valid_path_types": valid_path_types},
        )

    # Check if directory exists
    if not os.path.exists(path):
        return error_response(
            "NOT_FOUND", f"Path '{path}' does not exist", context={"path": path, "path_type": path_type}
        )

    setting_key = "LocalCachePath" if path_type == "local" else "NetworkCachePath"

    try:
        result = current_project.SetSetting(setting_key, path)
        if result:
            return success_response(
                {"path_type": path_type, "path": path}, message=f"Successfully set {path_type} cache path to '{path}'"
            )
        else:
            return error_response(
                "OPERATION_FAILED",
                f"Failed to set {path_type} cache path to '{path}'",
                context={"path_type": path_type, "path": path},
            )
    except Exception as e:
        return error_response(
            "OPERATION_FAILED", f"Error setting cache path: {str(e)}", context={"path_type": path_type, "path": path}
        )


@tool()
def generate_optimized_media(clip_names: List[str] = None) -> Dict[str, Any]:
    """Generate optimized media for specified clips or all clips if none specified.

    Args:
        clip_names: Optional list of clip names. If None, processes all clips in media pool
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("NO_PROJECT", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return error_response("OPERATION_FAILED", "Failed to get Media Pool")

    # Get clips to process
    if clip_names:
        # Get specified clips
        all_clips = get_all_media_pool_clips(media_pool)
        clips_to_process = []
        missing_clips = []

        for name in clip_names:
            found = False
            for clip in all_clips:
                if clip.GetName() == name:
                    clips_to_process.append(clip)
                    found = True
                    break
            if not found:
                missing_clips.append(name)

        if missing_clips:
            return error_response(
                "NOT_FOUND",
                f"Could not find these clips: {', '.join(missing_clips)}",
                context={"missing_clips": missing_clips},
            )

        if not clips_to_process:
            return error_response("NOT_FOUND", "No valid clips found to process", context={"clip_names": clip_names})
    else:
        # Get all clips
        clips_to_process = get_all_media_pool_clips(media_pool)

    try:
        # Select the clips
        media_pool.SetCurrentFolder(media_pool.GetRootFolder())
        for clip in clips_to_process:
            clip.AddFlag("Green")  # Temporarily add flag to help with selection

        # Switch to Media page if not already there
        current_page = resolve.GetCurrentPage()
        if current_page != "media":
            resolve.OpenPage("media")

        # Select clips with Green flag
        media_pool.SetClipSelection([clip for clip in clips_to_process])

        # Generate optimized media
        result = current_project.GenerateOptimizedMedia()

        # Remove temporary flags
        for clip in clips_to_process:
            clip.ClearFlags("Green")

        if result:
            return success_response(
                {"clip_count": len(clips_to_process)},
                message=f"Successfully started optimized media generation for {len(clips_to_process)} clips",
            )
        else:
            return error_response("OPERATION_FAILED", "Failed to start optimized media generation")
    except Exception as e:
        # Clean up flags in case of error
        try:
            for clip in clips_to_process:
                clip.ClearFlags("Green")
        except Exception:
            pass
        return error_response("OPERATION_FAILED", f"Error generating optimized media: {str(e)}")


@tool()
def delete_optimized_media(clip_names: List[str] = None) -> Dict[str, Any]:
    """Delete optimized media for specified clips or all clips if none specified.

    Args:
        clip_names: Optional list of clip names. If None, processes all clips in media pool
    """
    if resolve is None:
        return error_response(
            "NOT_CONNECTED",
            "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
        )

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("NO_PROJECT", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    media_pool = current_project.GetMediaPool()
    if not media_pool:
        return error_response("OPERATION_FAILED", "Failed to get Media Pool")

    # Get clips to process
    if clip_names:
        # Get specified clips
        all_clips = get_all_media_pool_clips(media_pool)
        clips_to_process = []
        missing_clips = []

        for name in clip_names:
            found = False
            for clip in all_clips:
                if clip.GetName() == name:
                    clips_to_process.append(clip)
                    found = True
                    break
            if not found:
                missing_clips.append(name)

        if missing_clips:
            return error_response(
                "NOT_FOUND",
                f"Could not find these clips: {', '.join(missing_clips)}",
                context={"missing_clips": missing_clips},
            )

        if not clips_to_process:
            return error_response("NOT_FOUND", "No valid clips found to process", context={"clip_names": clip_names})
    else:
        # Get all clips
        clips_to_process = get_all_media_pool_clips(media_pool)

    try:
        # Select the clips
        media_pool.SetCurrentFolder(media_pool.GetRootFolder())
        for clip in clips_to_process:
            clip.AddFlag("Green")  # Temporarily add flag to help with selection

        # Switch to Media page if not already there
        current_page = resolve.GetCurrentPage()
        if current_page != "media":
            resolve.OpenPage("media")

        # Select clips with Green flag
        media_pool.SetClipSelection([clip for clip in clips_to_process])

        # Delete optimized media
        result = current_project.DeleteOptimizedMedia()

        # Remove temporary flags
        for clip in clips_to_process:
            clip.ClearFlags("Green")

        if result:
            return success_response(
                {"clip_count": len(clips_to_process)},
                message=f"Successfully deleted optimized media for {len(clips_to_process)} clips",
            )
        else:
            return error_response("OPERATION_FAILED", "Failed to delete optimized media")
    except Exception as e:
        # Clean up flags in case of error
        try:
            for clip in clips_to_process:
                clip.ClearFlags("Green")
        except Exception:
            pass
        return error_response("OPERATION_FAILED", f"Error deleting optimized media: {str(e)}")


def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
