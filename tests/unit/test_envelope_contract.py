"""Invoke every registered tool with resolve=None and verify the envelope shape.

With no DaVinci Resolve connection, every tool should hit the NOT_CONNECTED
early return and produce a valid error envelope.  This test catches any tool
that accidentally returns a raw string, ad-hoc dict, or otherwise breaks
the {ok, data, error, message?, context?} contract.

The only exception is debug_environment, which returns system diagnostics
regardless of connection state.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

_stub = types.ModuleType("DaVinciResolveScript")
_stub.scriptapp = MagicMock(return_value=None)
sys.modules.setdefault("DaVinciResolveScript", _stub)

from davinci_resolve_mcp.server import create_server  # noqa: E402

DUMMY_ARGS = {
    "str": "test",
    "int": 0,
    "float": 0.0,
    "bool": False,
}

TOOL_REQUIRED_PARAMS = {
    "add_clip_to_timeline": [("clip_name", "str")],
    "add_fusion_effect": [("timeline_item_id", "str"), ("effect_name", "str")],
    "add_fusion_generator": [("timeline_item_id", "str"), ("generator_name", "str")],
    "add_keyframe": [("timeline_item_id", "str"), ("property_name", "str"), ("frame", "int"), ("value", "float")],
    "add_marker": [],
    "add_node": [],
    "add_to_render_queue": [("preset_name", "str")],
    "add_to_render_queue_json": [("preset_name", "str")],
    "add_user_to_cloud_project_tool": [("cloud_id", "str"), ("user_email", "str")],
    "apply_color_preset": [],
    "apply_lut": [("lut_path", "str")],
    "auto_sync_audio": [("clip_names", "str")],
    "clear_folder_transcription": [("folder_name", "str")],
    "clear_render_queue": [],
    "clear_transcription": [("clip_name", "str")],
    "close_project": [],
    "copy_grade": [],
    "create_bin": [("name", "str")],
    "create_cloud_project_tool": [("project_name", "str")],
    "create_color_preset_album": [("album_name", "str")],
    "create_empty_timeline": [("name", "str")],
    "create_project": [("name", "str")],
    "create_sub_clip": [("clip_name", "str"), ("start_frame", "int"), ("end_frame", "int")],
    "create_timeline": [("name", "str")],
    "create_timeline_from_clips": [("timeline_name", "str"), ("clip_names", "str")],
    "delete_color_preset": [],
    "delete_color_preset_album": [("album_name", "str")],
    "delete_keyframe": [("timeline_item_id", "str"), ("property_name", "str"), ("frame", "int")],
    "delete_layout_preset_tool": [("preset_name", "str")],
    "delete_media": [("clip_name", "str")],
    "delete_optimized_media": [],
    "delete_timeline": [("name", "str")],
    "enable_keyframes": [("timeline_item_id", "str")],
    "export_all_powergrade_luts": [("export_dir", "str")],
    "export_folder": [("folder_name", "str"), ("export_path", "str")],
    "export_layout_preset_tool": [("preset_name", "str"), ("export_path", "str")],
    "export_lut": [],
    "export_project_to_cloud_tool": [],
    "generate_optimized_media": [],
    "import_cloud_project_tool": [("cloud_id", "str")],
    "import_layout_preset_tool": [("import_path", "str")],
    "import_media": [("file_path", "str")],
    "inspect_custom_object": [("object_path", "str")],
    "link_proxy_media": [("clip_name", "str"), ("proxy_file_path", "str")],
    "list_media_pool_items": [],
    "list_timelines_tool": [],
    "load_layout_preset_tool": [("preset_name", "str")],
    "modify_keyframe": [("timeline_item_id", "str"), ("property_name", "str"), ("frame", "int")],
    "move_media_to_bin": [("clip_name", "str"), ("bin_name", "str")],
    "object_help": [("object_type", "str")],
    "open_app_preferences": [],
    "open_project": [("name", "str")],
    "open_settings": [],
    "quit_app": [],
    "razor_timeline": [],
    "relink_clips": [("clip_names", "str")],
    "remove_user_from_cloud_project_tool": [("cloud_id", "str"), ("user_email", "str")],
    "replace_clip": [("clip_name", "str"), ("replacement_path", "str")],
    "restart_app": [],
    "restore_cloud_project_tool": [("cloud_id", "str")],
    "save_color_preset": [],
    "save_layout_preset_tool": [("preset_name", "str")],
    "save_project": [],
    "set_cache_mode": [("mode", "str")],
    "set_cache_path": [("path_type", "str"), ("path", "str")],
    "set_color_science_mode_tool": [("mode", "str")],
    "set_color_space_tool": [("color_space", "str")],
    "set_color_wheel_param": [("wheel", "str"), ("param", "str"), ("value", "float")],
    "set_current_frame": [("frame", "int")],
    "set_current_timeline": [("name", "str")],
    "set_keyframe_interpolation": [
        ("timeline_item_id", "str"),
        ("property_name", "str"),
        ("frame", "int"),
        ("interpolation_type", "str"),
    ],
    "set_optimized_media_mode": [("mode", "str")],
    "set_project_property_tool": [("property_name", "str"), ("property_value", "str")],
    "set_project_setting": [("setting_name", "str"), ("setting_value", "str")],
    "set_proxy_mode": [("mode", "str")],
    "set_proxy_quality": [("quality", "str")],
    "set_superscale_settings_tool": [("enabled", "bool")],
    "set_timeline_format_tool": [("width", "int"), ("height", "int"), ("frame_rate", "float")],
    "set_timeline_item_audio": [("timeline_item_id", "str")],
    "set_timeline_item_composite": [("timeline_item_id", "str")],
    "set_timeline_item_crop": [("timeline_item_id", "str"), ("crop_type", "str"), ("crop_value", "float")],
    "set_timeline_item_name": [("timeline_item_id", "str"), ("name", "str")],
    "set_timeline_item_retime": [("timeline_item_id", "str")],
    "set_timeline_item_stabilization": [("timeline_item_id", "str")],
    "set_timeline_item_transform": [("timeline_item_id", "str"), ("property_name", "str"), ("property_value", "float")],
    "start_render": [],
    "switch_page": [("page", "str")],
    "transcribe_audio": [("clip_name", "str")],
    "transcribe_folder_audio": [("folder_name", "str")],
    "unlink_clips": [("clip_names", "str")],
    "unlink_proxy_media": [("clip_name", "str")],
}

SPECIAL_TOOLS = {"debug_environment"}


def _validate_envelope(result, tool_name):
    """Assert result is a valid response envelope dict."""
    assert isinstance(result, dict), f"{tool_name}: returned {type(result).__name__}, expected dict"
    assert "ok" in result, f"{tool_name}: missing 'ok' key — got keys {sorted(result.keys())}"
    assert isinstance(result["ok"], bool), f"{tool_name}: 'ok' is {type(result['ok']).__name__}, expected bool"

    if result["ok"]:
        assert result.get("error") is None, f"{tool_name}: ok=True but error is set"
    else:
        assert "error" in result and result["error"] is not None, f"{tool_name}: ok=False but no error"
        err = result["error"]
        assert isinstance(err, dict), f"{tool_name}: error is {type(err).__name__}, expected dict"
        assert "code" in err, f"{tool_name}: error missing 'code'"
        assert "message" in err, f"{tool_name}: error missing 'message'"
        assert isinstance(err["code"], str), f"{tool_name}: error code is not str"
        assert isinstance(err["message"], str), f"{tool_name}: error message is not str"


def test_all_tools_return_envelope_on_no_connection():
    """Call every tool with resolve=None and verify the envelope contract."""
    server = create_server()
    tools = server._tool_manager._tools

    tested = 0
    failures = []

    for tool_name, params in sorted(TOOL_REQUIRED_PARAMS.items()):
        if tool_name not in tools:
            continue

        kwargs = {name: DUMMY_ARGS[typ] for name, typ in params}
        tool_fn = tools[tool_name].fn

        try:
            result = tool_fn(**kwargs)
        except Exception as exc:
            failures.append(f"{tool_name}: raised {type(exc).__name__}: {exc}")
            continue

        try:
            _validate_envelope(result, tool_name)
            assert result["ok"] is False, f"{tool_name}: expected ok=False with no Resolve connection"
        except AssertionError as exc:
            failures.append(str(exc))
            continue

        tested += 1

    assert not failures, "Envelope contract violations:\n" + "\n".join(failures)
    assert tested >= 80, f"Only tested {tested} tools — expected at least 80"


def test_debug_environment_returns_success_envelope():
    """debug_environment works without a connection and returns ok=True."""
    server = create_server()
    tools = server._tool_manager._tools
    result = tools["debug_environment"].fn()
    _validate_envelope(result, "debug_environment")
    assert result["ok"] is True, "debug_environment should succeed without Resolve"
    assert result["data"] is not None, "debug_environment should return system data"
