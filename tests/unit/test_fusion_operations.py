"""Unit tests for davinci_resolve_mcp.api.fusion_operations.

Resolve is mocked entirely.  The Fusion wiring branches in
add_fusion_effect / add_fusion_generator are exercised at the
"item-not-found" boundary and along a happy path with a minimal
fake comp; the deep Lua keyframe paths are out of scope.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from davinci_resolve_mcp.api import fusion_operations as ops


def _fake_item(unique_id="ID-1", name="Clip", fusion_comp=None):
    item = MagicMock()
    item.GetUniqueId.return_value = unique_id
    item.GetName.return_value = name
    if fusion_comp is None:
        item.GetFusionCompCount.return_value = 0
    else:
        item.GetFusionCompCount.return_value = 1
        item.GetFusionCompByIndex.return_value = fusion_comp
    return item


def _resolve_with_video_items(items_per_track):
    """Build a MagicMock resolve whose current timeline has the given video tracks."""
    timeline = MagicMock()
    timeline.GetTrackCount.return_value = len(items_per_track)

    def get_items(track_type, track_index):
        if track_type != "video":
            return []
        return items_per_track[track_index - 1] if 1 <= track_index <= len(items_per_track) else []

    timeline.GetItemListInTrack.side_effect = get_items

    project = MagicMock()
    project.GetCurrentTimeline.return_value = timeline
    pm = MagicMock()
    pm.GetCurrentProject.return_value = project
    resolve = MagicMock()
    resolve.GetProjectManager.return_value = pm
    return resolve, timeline


# ---------------------------------------------------------------------------
# get_item_by_id
# ---------------------------------------------------------------------------

def test_get_item_by_id_returns_none_when_no_timeline():
    project = MagicMock()
    project.GetCurrentTimeline.return_value = None
    pm = MagicMock()
    pm.GetCurrentProject.return_value = project
    resolve = MagicMock()
    resolve.GetProjectManager.return_value = pm
    assert ops.get_item_by_id(resolve, "anything") is None


def test_get_item_by_id_finds_by_unique_id():
    target = _fake_item(unique_id="ABC")
    other = _fake_item(unique_id="XYZ")
    resolve, _ = _resolve_with_video_items([[other, target]])
    assert ops.get_item_by_id(resolve, "ABC") is target


def test_get_item_by_id_falls_back_to_name_match():
    """When UniqueId throws, fusion_operations falls back to GetName()."""
    target = MagicMock()
    target.GetUniqueId.side_effect = RuntimeError("no unique id")
    target.GetName.return_value = "MyClip"
    resolve, _ = _resolve_with_video_items([[target]])
    assert ops.get_item_by_id(resolve, "MyClip") is target


def test_get_item_by_id_returns_none_when_no_match():
    other = _fake_item(unique_id="XYZ", name="OtherClip")
    resolve, _ = _resolve_with_video_items([[other]])
    assert ops.get_item_by_id(resolve, "missing") is None


def test_get_item_by_id_searches_all_video_tracks():
    target = _fake_item(unique_id="ABC")
    resolve, _ = _resolve_with_video_items([[], [target]])  # second track
    assert ops.get_item_by_id(resolve, "ABC") is target


# ---------------------------------------------------------------------------
# add_fusion_effect
# ---------------------------------------------------------------------------

def test_add_fusion_effect_item_not_found():
    resolve, _ = _resolve_with_video_items([[]])
    assert ops.add_fusion_effect(resolve, "missing", "Vignette") == (
        "Error: Timeline item 'missing' not found."
    )


def test_add_fusion_effect_comp_creation_failure():
    """If AddFusionComp() doesn't produce a comp, we surface a clean error."""
    item = MagicMock()
    item.GetUniqueId.return_value = "ABC"
    item.GetName.return_value = "Clip"
    item.GetFusionCompCount.return_value = 0
    # AddFusionComp does nothing and count stays 0.
    resolve, _ = _resolve_with_video_items([[item]])
    result = ops.add_fusion_effect(resolve, "ABC", "Vignette")
    assert result == "Error: Failed to create/access Fusion Composition."


def test_add_fusion_effect_tool_add_failure():
    """If comp.AddTool returns falsy, we report a clean error and don't continue."""
    comp = MagicMock()
    comp.AddTool.return_value = None
    item = _fake_item(unique_id="ABC", fusion_comp=comp)
    resolve, _ = _resolve_with_video_items([[item]])
    result = ops.add_fusion_effect(resolve, "ABC", "BogusTool")
    assert result == "Error: Failed to add tool 'BogusTool'. Check if name is correct."


def test_add_fusion_effect_success_with_settings_and_wiring():
    """Happy path: tool added, simple SetInput call, and wiring between MediaIn/MediaOut."""
    new_tool = MagicMock()
    new_tool.Name = "Vignette1"
    new_tool.FindMainOutput.return_value = "vignette-output"

    media_in = MagicMock()
    media_in.ID = "MediaIn"
    media_in.Name = "MediaIn1"
    media_in.FindMainOutput.return_value = "mediain-output"

    media_out = MagicMock()
    media_out.ID = "MediaOut"
    media_out.Name = "MediaOut1"
    media_out.GetInput.return_value = "current-source"  # something already feeding MediaOut

    comp = MagicMock()
    comp.AddTool.return_value = new_tool
    comp.GetToolList.return_value = {
        "MediaIn1": media_in,
        "Vignette1": new_tool,
        "MediaOut1": media_out,
    }
    comp.GetAttrs.return_value = {"COMPS_Name": "Comp 1"}

    item = _fake_item(unique_id="ABC", fusion_comp=comp)
    resolve, _ = _resolve_with_video_items([[item]])
    result = ops.add_fusion_effect(resolve, "ABC", "Vignette", settings={"Gain": 2.0})

    assert result.startswith("Successfully added 'Vignette'")
    new_tool.SetInput.assert_any_call("Gain", 2.0)
    # The pipeline insertion: NewTool gets the previous MediaOut input,
    # and MediaOut now points at the new tool's output.
    new_tool.SetInput.assert_any_call("Input", "current-source")
    media_out.SetInput.assert_called_once_with("Input", "vignette-output")


# ---------------------------------------------------------------------------
# add_fusion_generator
# ---------------------------------------------------------------------------

def test_add_fusion_generator_no_timeline():
    project = MagicMock()
    project.GetCurrentTimeline.return_value = None
    pm = MagicMock()
    pm.GetCurrentProject.return_value = project
    resolve = MagicMock()
    resolve.GetProjectManager.return_value = pm
    assert ops.add_fusion_generator(resolve, "ABC", "TextPlus") == "Error: No current timeline"


def test_add_fusion_generator_item_not_found():
    resolve, _ = _resolve_with_video_items([[]])
    assert ops.add_fusion_generator(resolve, "missing", "TextPlus") == (
        "Error: Timeline item missing not found"
    )


def test_add_fusion_generator_success_wires_via_merge():
    gen_tool = MagicMock()
    gen_tool.FindMainOutput.return_value = "gen-output"
    merge_tool = MagicMock()
    merge_tool.FindMainOutput.return_value = "merge-output"

    media_in = MagicMock()
    media_in.ID = "MediaIn"
    media_in.Name = "MediaIn1"
    media_in.FindMainOutput.return_value = "mediain-output"

    media_out = MagicMock()
    media_out.ID = "MediaOut"
    media_out.Name = "MediaOut1"
    media_out.GetInput.return_value = None  # nothing currently feeding MediaOut → fall back to MediaIn

    comp = MagicMock()
    # First AddTool is the generator, second is the Merge node.
    comp.AddTool.side_effect = [gen_tool, merge_tool]
    comp.GetToolList.return_value = {
        "MediaIn1": media_in,
        "TextPlus1": gen_tool,
        "Merge1": merge_tool,
        "MediaOut1": media_out,
    }

    item = _fake_item(unique_id="ABC", fusion_comp=comp)
    resolve, _ = _resolve_with_video_items([[item]])

    assert ops.add_fusion_generator(resolve, "ABC", "TextPlus") == "Added generator 'TextPlus'"
    # Generator on Foreground, MediaIn on Background, Merge feeding MediaOut.
    merge_tool.SetInput.assert_any_call("Background", "mediain-output")
    merge_tool.SetInput.assert_any_call("Foreground", "gen-output")
    media_out.SetInput.assert_called_once_with("Input", "merge-output")


def test_add_fusion_generator_no_media_out_returns_error():
    gen_tool = MagicMock()
    merge_tool = MagicMock()
    comp = MagicMock()
    comp.AddTool.side_effect = [gen_tool, merge_tool]
    comp.GetToolList.return_value = {}  # no MediaIn / MediaOut at all

    item = _fake_item(unique_id="ABC", fusion_comp=comp)
    resolve, _ = _resolve_with_video_items([[item]])

    assert ops.add_fusion_generator(resolve, "ABC", "TextPlus") == (
        "Error: Could not find MediaOut to wire generator"
    )
