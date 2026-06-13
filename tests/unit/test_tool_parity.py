"""Verify the modular server registers all expected tools and resources.

This test constructs a FastMCP server via create_server() with a mocked
DaVinciResolveScript and asserts the registered tool/resource names match
a frozen manifest.  It guards against accidental tool loss during the
monolith-to-modular migration.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

# Stub DaVinciResolveScript before any davinci_resolve_mcp import
_stub = types.ModuleType("DaVinciResolveScript")
_stub.scriptapp = MagicMock(return_value=None)
sys.modules["DaVinciResolveScript"] = _stub

from davinci_resolve_mcp.server import create_server  # noqa: E402


EXPECTED_TOOLS = {
    "add_clip_to_timeline",
    "add_fusion_effect",
    "add_fusion_generator",
    "add_keyframe",
    "add_marker",
    "add_node",
    "add_to_render_queue",
    "add_to_render_queue_json",
    "add_user_to_cloud_project_tool",
    "apply_color_preset",
    "apply_lut",
    "auto_sync_audio",
    "clear_folder_transcription",
    "clear_render_queue",
    "clear_transcription",
    "close_project",
    "copy_grade",
    "create_bin",
    "create_cloud_project_tool",
    "create_color_preset_album",
    "create_empty_timeline",
    "create_project",
    "create_sub_clip",
    "create_timeline",
    "create_timeline_from_clips",
    "debug_environment",
    "delete_color_preset",
    "delete_color_preset_album",
    "delete_keyframe",
    "delete_layout_preset_tool",
    "delete_media",
    "delete_optimized_media",
    "delete_timeline",
    "enable_keyframes",
    "export_all_powergrade_luts",
    "export_folder",
    "export_layout_preset_tool",
    "export_lut",
    "export_project_to_cloud_tool",
    "generate_optimized_media",
    "import_cloud_project_tool",
    "import_layout_preset_tool",
    "import_media",
    "inspect_custom_object",
    "link_proxy_media",
    "list_media_pool_items",
    "list_timelines_tool",
    "load_layout_preset_tool",
    "modify_keyframe",
    "move_media_to_bin",
    "object_help",
    "open_app_preferences",
    "open_project",
    "open_settings",
    "quit_app",
    "razor_timeline",
    "relink_clips",
    "remove_user_from_cloud_project_tool",
    "replace_clip",
    "restart_app",
    "restore_cloud_project_tool",
    "save_color_preset",
    "save_layout_preset_tool",
    "save_project",
    "set_cache_mode",
    "set_cache_path",
    "set_color_science_mode_tool",
    "set_color_space_tool",
    "set_color_wheel_param",
    "set_current_frame",
    "set_current_timeline",
    "set_keyframe_interpolation",
    "set_optimized_media_mode",
    "set_project_property_tool",
    "set_project_setting",
    "set_proxy_mode",
    "set_proxy_quality",
    "set_superscale_settings_tool",
    "set_timeline_format_tool",
    "set_timeline_item_audio",
    "set_timeline_item_composite",
    "set_timeline_item_crop",
    "set_timeline_item_name",
    "set_timeline_item_retime",
    "set_timeline_item_stabilization",
    "set_timeline_item_transform",
    "start_render",
    "switch_page",
    "transcribe_audio",
    "transcribe_folder_audio",
    "unlink_clips",
    "unlink_proxy_media",
}

EXPECTED_RESOURCES = {
    "resolve://app/state",
    "resolve://cache/settings",
    "resolve://cloud/projects",
    "resolve://color/current-node",
    "resolve://color/lut-formats",
    "resolve://color/presets",
    "resolve://current-page",
    "resolve://current-project",
    "resolve://current-timeline",
    "resolve://delivery/render-presets",
    "resolve://delivery/render-queue/status",
    "resolve://inspect/current-project",
    "resolve://inspect/current-timeline",
    "resolve://inspect/media-pool",
    "resolve://inspect/project-manager",
    "resolve://inspect/resolve",
    "resolve://layout-presets",
    "resolve://media-pool-bins",
    "resolve://media-pool-clips",
    "resolve://project-settings",
    "resolve://project/color-settings",
    "resolve://project/info",
    "resolve://project/metadata",
    "resolve://project/properties",
    "resolve://project/superscale",
    "resolve://project/timeline-format",
    "resolve://projects",
    "resolve://timeline-clips",
    "resolve://timeline-items",
    "resolve://timeline-items-list",
    "resolve://timelines",
    "resolve://version",
}


def test_tool_parity():
    server = create_server()
    registered = set(server._tool_manager._tools.keys())
    missing = EXPECTED_TOOLS - registered
    assert not missing, f"Tools missing from modular server: {sorted(missing)}"


def test_resource_parity():
    server = create_server()
    registered = set(server._resource_manager._resources.keys())
    missing = EXPECTED_RESOURCES - registered
    assert not missing, f"Resources missing from modular server: {sorted(missing)}"
