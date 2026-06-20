"""Handlers for color preset and LUT utilities."""

from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers
from davinci_resolve_mcp.utils.response import success_response, error_response

logger = logging.getLogger("davinci-resolve-mcp.color_presets")
registry = HandlerRegistry()
resource = registry.resource
tool = registry.tool
resolve: Optional[Any] = None


@resource("resolve://color/presets")
def get_color_presets() -> List[Dict[str, Any]]:
    """Get all available color presets in the current project."""
    if resolve is None:
        return [{"error": "Not connected to DaVinci Resolve"}]

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return [{"error": "Failed to get Project Manager"}]

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return [{"error": "No project currently open"}]

    # Switch to color page to access presets
    current_page = resolve.GetCurrentPage()
    if current_page != "color":
        resolve.OpenPage("color")

    try:
        # Get gallery
        gallery = current_project.GetGallery()
        if not gallery:
            return [{"error": "Failed to get gallery"}]

        # Get all albums
        albums = gallery.GetAlbums()
        if not albums:
            return [{"info": "No albums found in gallery"}]

        result = []
        for album in albums:
            # Get stills in the album
            stills = album.GetStills()
            album_info = {"name": album.GetName(), "stills": []}

            if stills:
                for still in stills:
                    still_info = {
                        "id": still.GetUniqueId(),
                        "label": still.GetLabel(),
                        "timecode": still.GetTimecode(),
                        "isGrabbed": still.IsGrabbed(),
                    }
                    album_info["stills"].append(still_info)

            result.append(album_info)

        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)

        return result

    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return [{"error": f"Error retrieving color presets: {str(e)}"}]


@tool()
def save_color_preset(
    clip_name: str = None, preset_name: str = None, album_name: str = "DaVinci Resolve"
) -> Dict[str, Any]:
    """Save a color preset from the specified clip.

    Args:
        clip_name: Name of the clip to save preset from (uses current clip if None)
        preset_name: Name to give the preset (uses clip name if None)
        album_name: Album to save the preset to (default: "DaVinci Resolve")
    """
    if resolve is None:
        return error_response("NOT_CONNECTED", "Not connected to DaVinci Resolve")

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    # Switch to color page
    current_page = resolve.GetCurrentPage()
    if current_page != "color":
        resolve.OpenPage("color")

    try:
        # Get the current timeline
        current_timeline = current_project.GetCurrentTimeline()
        if not current_timeline:
            return error_response("NO_TIMELINE", "No timeline is currently open")

        # Get the specific clip or current clip
        if clip_name:
            # Find the clip by name in the timeline
            timeline_clips = current_timeline.GetItemListInTrack("video", 1)
            target_clip = None

            for clip in timeline_clips:
                if clip.GetName() == clip_name:
                    target_clip = clip
                    break

            if not target_clip:
                return error_response("NOT_FOUND", f"Clip '{clip_name}' not found in the timeline")

            # Select the clip
            current_timeline.SetCurrentSelectedItem(target_clip)

        # Get gallery
        gallery = current_project.GetGallery()
        if not gallery:
            return error_response("OPERATION_FAILED", "Failed to get gallery")

        # Get or create album
        album = None
        albums = gallery.GetAlbums()

        if albums:
            for a in albums:
                if a.GetName() == album_name:
                    album = a
                    break

        if not album:
            # Create a new album if it doesn't exist
            album = gallery.CreateAlbum(album_name)
            if not album:
                return error_response("OPERATION_FAILED", f"Failed to create album '{album_name}'")

        # Set preset name if specified
        final_preset_name = preset_name
        if not final_preset_name:
            if clip_name:
                final_preset_name = f"{clip_name} Preset"
            else:
                # Get current clip name if available
                current_clip = current_timeline.GetCurrentVideoItem()
                if current_clip:
                    final_preset_name = f"{current_clip.GetName()} Preset"
                else:
                    final_preset_name = f"Preset {len(album.GetStills()) + 1}"

        # Capture still
        result = gallery.GrabStill()

        if not result:
            return error_response("OPERATION_FAILED", "Failed to grab still for the preset")

        # Get the still that was just created
        stills = album.GetStills()
        if stills:
            latest_still = stills[-1]  # Assume the last one is the one we just grabbed
            # Set the label
            latest_still.SetLabel(final_preset_name)

        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)

        return success_response(
            message=f"Saved color preset '{final_preset_name}' to album '{album_name}'",
            context={"preset_name": final_preset_name, "album_name": album_name, "clip_name": clip_name},
        )

    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return error_response("OPERATION_FAILED", f"Error saving color preset: {str(e)}")


@tool()
def apply_color_preset(
    preset_id: str = None, preset_name: str = None, clip_name: str = None, album_name: str = "DaVinci Resolve"
) -> Dict[str, Any]:
    """Apply a color preset to the specified clip.

    Args:
        preset_id: ID of the preset to apply (if known)
        preset_name: Name of the preset to apply (searches in album)
        clip_name: Name of the clip to apply preset to (uses current clip if None)
        album_name: Album containing the preset (default: "DaVinci Resolve")
    """
    if resolve is None:
        return error_response("NOT_CONNECTED", "Not connected to DaVinci Resolve")

    if not preset_id and not preset_name:
        return error_response("INVALID_ARG", "Must provide either preset_id or preset_name")

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    # Switch to color page
    current_page = resolve.GetCurrentPage()
    if current_page != "color":
        resolve.OpenPage("color")

    try:
        # Get the current timeline
        current_timeline = current_project.GetCurrentTimeline()
        if not current_timeline:
            return error_response("NO_TIMELINE", "No timeline is currently open")

        # Get the specific clip or current clip
        if clip_name:
            # Find the clip by name in the timeline
            timeline_clips = current_timeline.GetItemListInTrack("video", 1)
            target_clip = None

            for clip in timeline_clips:
                if clip.GetName() == clip_name:
                    target_clip = clip
                    break

            if not target_clip:
                return error_response("NOT_FOUND", f"Clip '{clip_name}' not found in the timeline")

            # Select the clip
            current_timeline.SetCurrentSelectedItem(target_clip)

        # Get gallery
        gallery = current_project.GetGallery()
        if not gallery:
            return error_response("OPERATION_FAILED", "Failed to get gallery")

        # Find the album
        album = None
        albums = gallery.GetAlbums()

        if albums:
            for a in albums:
                if a.GetName() == album_name:
                    album = a
                    break

        if not album:
            return error_response("NOT_FOUND", f"Album '{album_name}' not found")

        # Find the still to apply
        stills = album.GetStills()
        if not stills:
            return error_response("NOT_FOUND", f"No presets found in album '{album_name}'")

        target_still = None

        if preset_id:
            # Find by ID
            for still in stills:
                if still.GetUniqueId() == preset_id:
                    target_still = still
                    break
        elif preset_name:
            # Find by name
            for still in stills:
                if still.GetLabel() == preset_name:
                    target_still = still
                    break

        if not target_still:
            search_term = preset_id if preset_id else preset_name
            return error_response("NOT_FOUND", f"Preset '{search_term}' not found in album '{album_name}'")

        # Apply the preset
        result = target_still.ApplyToClip()

        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)

        if result:
            return success_response(
                message=f"Applied color preset to {'specified clip' if clip_name else 'current clip'}",
                context={
                    "preset_id": preset_id,
                    "preset_name": preset_name,
                    "clip_name": clip_name,
                    "album_name": album_name,
                },
            )
        else:
            return error_response("OPERATION_FAILED", "Failed to apply color preset")

    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return error_response("OPERATION_FAILED", f"Error applying color preset: {str(e)}")


@tool()
def delete_color_preset(
    preset_id: str = None, preset_name: str = None, album_name: str = "DaVinci Resolve"
) -> Dict[str, Any]:
    """Delete a color preset.

    Args:
        preset_id: ID of the preset to delete (if known)
        preset_name: Name of the preset to delete (searches in album)
        album_name: Album containing the preset (default: "DaVinci Resolve")
    """
    if resolve is None:
        return error_response("NOT_CONNECTED", "Not connected to DaVinci Resolve")

    if not preset_id and not preset_name:
        return error_response("INVALID_ARG", "Must provide either preset_id or preset_name")

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    # Switch to color page
    current_page = resolve.GetCurrentPage()
    if current_page != "color":
        resolve.OpenPage("color")

    try:
        # Get gallery
        gallery = current_project.GetGallery()
        if not gallery:
            return error_response("OPERATION_FAILED", "Failed to get gallery")

        # Find the album
        album = None
        albums = gallery.GetAlbums()

        if albums:
            for a in albums:
                if a.GetName() == album_name:
                    album = a
                    break

        if not album:
            return error_response("NOT_FOUND", f"Album '{album_name}' not found")

        # Find the still to delete
        stills = album.GetStills()
        if not stills:
            return error_response("NOT_FOUND", f"No presets found in album '{album_name}'")

        target_still = None

        if preset_id:
            # Find by ID
            for still in stills:
                if still.GetUniqueId() == preset_id:
                    target_still = still
                    break
        elif preset_name:
            # Find by name
            for still in stills:
                if still.GetLabel() == preset_name:
                    target_still = still
                    break

        if not target_still:
            search_term = preset_id if preset_id else preset_name
            return error_response("NOT_FOUND", f"Preset '{search_term}' not found in album '{album_name}'")

        # Delete the preset
        result = album.DeleteStill(target_still)

        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)

        if result:
            return success_response(
                message=f"Deleted color preset from album '{album_name}'",
                context={
                    "preset_id": preset_id,
                    "preset_name": preset_name,
                    "album_name": album_name,
                },
            )
        else:
            return error_response("OPERATION_FAILED", "Failed to delete color preset")

    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return error_response("OPERATION_FAILED", f"Error deleting color preset: {str(e)}")


@tool()
def create_color_preset_album(album_name: str) -> Dict[str, Any]:
    """Create a new album for color presets.

    Args:
        album_name: Name for the new album
    """
    if resolve is None:
        return error_response("NOT_CONNECTED", "Not connected to DaVinci Resolve")

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    # Switch to color page
    current_page = resolve.GetCurrentPage()
    if current_page != "color":
        resolve.OpenPage("color")

    try:
        # Get gallery
        gallery = current_project.GetGallery()
        if not gallery:
            return error_response("OPERATION_FAILED", "Failed to get gallery")

        # Check if album already exists
        albums = gallery.GetAlbums()

        if albums:
            for a in albums:
                if a.GetName() == album_name:
                    # Return to the original page if we switched
                    if current_page != "color":
                        resolve.OpenPage(current_page)
                    return error_response("OPERATION_FAILED", f"Album '{album_name}' already exists")

        # Create a new album
        album = gallery.CreateAlbum(album_name)

        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)

        if album:
            return success_response(
                message=f"Created album '{album_name}'",
                context={"album_name": album_name},
            )
        else:
            return error_response("OPERATION_FAILED", f"Failed to create album '{album_name}'")

    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return error_response("OPERATION_FAILED", f"Error creating album: {str(e)}")


@tool()
def delete_color_preset_album(album_name: str) -> Dict[str, Any]:
    """Delete a color preset album.

    Args:
        album_name: Name of the album to delete
    """
    if resolve is None:
        return error_response("NOT_CONNECTED", "Not connected to DaVinci Resolve")

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    # Switch to color page
    current_page = resolve.GetCurrentPage()
    if current_page != "color":
        resolve.OpenPage("color")

    try:
        # Get gallery
        gallery = current_project.GetGallery()
        if not gallery:
            return error_response("OPERATION_FAILED", "Failed to get gallery")

        # Find the album
        album = None
        albums = gallery.GetAlbums()

        if albums:
            for a in albums:
                if a.GetName() == album_name:
                    album = a
                    break

        if not album:
            # Return to the original page if we switched
            if current_page != "color":
                resolve.OpenPage(current_page)
            return error_response("NOT_FOUND", f"Album '{album_name}' not found")

        # Delete the album
        result = gallery.DeleteAlbum(album)

        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)

        if result:
            return success_response(
                message=f"Deleted album '{album_name}'",
                context={"album_name": album_name},
            )
        else:
            return error_response("OPERATION_FAILED", f"Failed to delete album '{album_name}'")

    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return error_response("OPERATION_FAILED", f"Error deleting album: {str(e)}")


@tool()
def export_lut(
    clip_name: str = None, export_path: str = None, lut_format: str = "Cube", lut_size: str = "33Point"
) -> Dict[str, Any]:
    """Export a LUT from the current clip's grade.

    Args:
        clip_name: Name of the clip to export grade from (uses current clip if None)
        export_path: Path to save the LUT file (generated if None)
        lut_format: Format of the LUT. Options: 'Cube', 'Davinci', '3dl', 'Panasonic'
        lut_size: Size of the LUT. Options: '17Point', '33Point', '65Point'
    """
    if resolve is None:
        return error_response("NOT_CONNECTED", "Not connected to DaVinci Resolve")

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    # Switch to color page
    current_page = resolve.GetCurrentPage()
    if current_page != "color":
        resolve.OpenPage("color")

    try:
        # Get the current timeline
        current_timeline = current_project.GetCurrentTimeline()
        if not current_timeline:
            return error_response("NO_TIMELINE", "No timeline is currently open")

        # Get the specific clip or current clip
        if clip_name:
            # Find the clip by name in the timeline
            timeline_clips = current_timeline.GetItemListInTrack("video", 1)
            target_clip = None

            for clip in timeline_clips:
                if clip.GetName() == clip_name:
                    target_clip = clip
                    break

            if not target_clip:
                return error_response("NOT_FOUND", f"Clip '{clip_name}' not found in the timeline")

            # Select the clip
            current_timeline.SetCurrentSelectedItem(target_clip)

        # Generate export path if not provided
        if not export_path:
            import tempfile

            clip_name_safe = clip_name if clip_name else "current_clip"
            clip_name_safe = clip_name_safe.replace(" ", "_").replace(":", "-")

            extension = ".cube"
            if lut_format.lower() == "davinci":
                extension = ".ilut"
            elif lut_format.lower() == "3dl":
                extension = ".3dl"
            elif lut_format.lower() == "panasonic":
                extension = ".vlut"

            export_path = os.path.join(tempfile.gettempdir(), f"{clip_name_safe}_lut{extension}")

        # Validate LUT format
        valid_formats = ["Cube", "Davinci", "3dl", "Panasonic"]
        if lut_format not in valid_formats:
            return error_response("INVALID_ARG", f"Invalid LUT format. Must be one of: {', '.join(valid_formats)}")

        # Validate LUT size
        valid_sizes = ["17Point", "33Point", "65Point"]
        if lut_size not in valid_sizes:
            return error_response("INVALID_ARG", f"Invalid LUT size. Must be one of: {', '.join(valid_sizes)}")

        # Map format string to numeric value expected by DaVinci Resolve API
        format_map = {"Cube": 0, "Davinci": 1, "3dl": 2, "Panasonic": 3}

        # Map size string to numeric value
        size_map = {"17Point": 0, "33Point": 1, "65Point": 2}

        # Get current clip
        current_clip = current_timeline.GetCurrentVideoItem()
        if not current_clip:
            return error_response("NO_TIMELINE", "No clip is currently selected")

        # Create a directory for the export path if it doesn't exist
        export_dir = os.path.dirname(export_path)
        if export_dir and not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)

        # Export the LUT
        colorpage = resolve.GetCurrentPage() == "color"
        if not colorpage:
            resolve.OpenPage("color")

        # Access Color page functionality
        result = current_project.ExportCurrentGradeAsLUT(format_map[lut_format], size_map[lut_size], export_path)

        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)

        if result:
            return success_response(
                message=f"Exported LUT to '{export_path}' in {lut_format} format with {lut_size} size",
                context={
                    "clip_name": clip_name,
                    "export_path": export_path,
                    "lut_format": lut_format,
                    "lut_size": lut_size,
                },
            )
        else:
            return error_response("OPERATION_FAILED", "Failed to export LUT")

    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return error_response("OPERATION_FAILED", f"Error exporting LUT: {str(e)}")


@resource("resolve://color/lut-formats")
def get_lut_formats() -> Dict[str, Any]:
    """Get available LUT export formats and sizes."""
    formats = {
        "formats": [
            {
                "name": "Cube",
                "extension": ".cube",
                "description": "Industry standard LUT format supported by most applications",
            },
            {"name": "Davinci", "extension": ".ilut", "description": "DaVinci Resolve's native LUT format"},
            {"name": "3dl", "extension": ".3dl", "description": "ASSIMILATE SCRATCH and some Autodesk applications"},
            {"name": "Panasonic", "extension": ".vlut", "description": "Panasonic VariCam and other Panasonic cameras"},
        ],
        "sizes": [
            {"name": "17Point", "description": "Smaller file size, less precision (17x17x17)"},
            {"name": "33Point", "description": "Standard size with good balance of precision and file size (33x33x33)"},
            {"name": "65Point", "description": "Highest precision but larger file size (65x65x65)"},
        ],
    }
    return formats


@tool()
def export_all_powergrade_luts(export_dir: str) -> Dict[str, Any]:
    """Export all PowerGrade presets as LUT files.

    Args:
        export_dir: Directory to save the exported LUTs
    """
    if resolve is None:
        return error_response("NOT_CONNECTED", "Not connected to DaVinci Resolve")

    project_manager = resolve.GetProjectManager()
    if not project_manager:
        return error_response("OPERATION_FAILED", "Failed to get Project Manager")

    current_project = project_manager.GetCurrentProject()
    if not current_project:
        return error_response("NO_PROJECT", "No project currently open")

    # Switch to color page
    current_page = resolve.GetCurrentPage()
    if current_page != "color":
        resolve.OpenPage("color")

    try:
        # Get gallery
        gallery = current_project.GetGallery()
        if not gallery:
            return error_response("OPERATION_FAILED", "Failed to get gallery")

        # Get PowerGrade album
        powergrade_album = None
        albums = gallery.GetAlbums()

        if albums:
            for album in albums:
                if album.GetName() == "PowerGrade":
                    powergrade_album = album
                    break

        if not powergrade_album:
            return error_response("NOT_FOUND", "PowerGrade album not found")

        # Get all stills in the PowerGrade album
        stills = powergrade_album.GetStills()
        if not stills:
            return error_response("NOT_FOUND", "No stills found in PowerGrade album")

        # Create export directory if it doesn't exist
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)

        current_timeline = current_project.GetCurrentTimeline()
        if not current_timeline:
            return error_response("NO_TIMELINE", "No timeline currently open")

        # Export each still as a LUT
        exported_count = 0
        failed_stills = []

        for still in stills:
            still_name = still.GetLabel()
            if not still_name:
                still_name = f"PowerGrade_{still.GetUniqueId()}"

            # Create safe filename
            safe_name = "".join(c if c.isalnum() or c in ["-", "_"] else "_" for c in still_name)
            lut_path = os.path.join(export_dir, f"{safe_name}.cube")

            # Apply the still to the current clip
            current_clip = current_timeline.GetCurrentVideoItem()
            if not current_clip:
                failed_stills.append(f"{still_name} (no clip selected)")
                continue

            # Apply the grade from the still
            applied = still.ApplyToClip()
            if not applied:
                failed_stills.append(f"{still_name} (could not apply grade)")
                continue

            # Export as LUT
            result = current_project.ExportCurrentGradeAsLUT(0, 1, lut_path)  # Cube format, 33-point

            if result:
                exported_count += 1
            else:
                failed_stills.append(f"{still_name} (export failed)")

        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)

        if failed_stills:
            return success_response(
                message=f"Exported {exported_count} LUTs to '{export_dir}'. Failed to export: {', '.join(failed_stills)}",
                context={"export_dir": export_dir, "exported_count": exported_count, "failed_stills": failed_stills},
            )
        else:
            return success_response(
                message=f"Exported all {exported_count} PowerGrade LUTs to '{export_dir}'",
                context={"export_dir": export_dir, "exported_count": exported_count},
            )

    except Exception as e:
        # Return to the original page if we switched
        if current_page != "color":
            resolve.OpenPage(current_page)
        return error_response("OPERATION_FAILED", f"Error exporting PowerGrade LUTs: {str(e)}")


def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module."""
    install_handlers(server, context, registry, globals())
