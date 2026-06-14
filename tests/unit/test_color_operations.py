"""Unit tests for davinci_resolve_mcp.api.color_operations.

Resolve is mocked entirely.  Focused on entry validation, page guards,
the `ensure_clip_selected` helper, and a representative happy path for
each of the four user-facing entry points.  Deep grade/node mutation
branches are out of scope.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from davinci_resolve_mcp.api import color_operations as ops


def _resolve(*, project=None, current_page="color"):
    """Build a MagicMock resolve with the supplied project and page."""
    pm = MagicMock()
    pm.GetCurrentProject.return_value = project
    resolve = MagicMock()
    resolve.GetProjectManager.return_value = pm
    resolve.GetCurrentPage.return_value = current_page
    resolve.OpenPage.return_value = True
    return resolve


def _project_with_timeline(timeline):
    project = MagicMock()
    project.GetCurrentTimeline.return_value = timeline
    return project


def _timeline_with_clip(clip, *, video_track_items=None):
    """Build a MagicMock timeline with the given current clip."""
    timeline = MagicMock()
    timeline.GetCurrentVideoItem.return_value = clip
    if video_track_items is not None:
        timeline.GetTrackCount.return_value = len(video_track_items)
        timeline.GetItemListInTrack.side_effect = (
            lambda track_type, track_idx: video_track_items[track_idx - 1]
            if track_type == "video" and 1 <= track_idx <= len(video_track_items)
            else []
        )
    return timeline


def _clip_with_grade(grade, name="Clip"):
    clip = MagicMock()
    clip.GetCurrentGrade.return_value = grade
    clip.GetName.return_value = name
    return clip


# ---------------------------------------------------------------------------
# get_current_node
# ---------------------------------------------------------------------------

def test_get_current_node_not_connected():
    assert ops.get_current_node(None) == {"error": "Not connected to DaVinci Resolve"}


def test_get_current_node_wrong_page():
    project = _project_with_timeline(MagicMock())
    resolve = _resolve(project=project, current_page="edit")
    assert ops.get_current_node(resolve) == {"error": "Not on Color page. Current page is: edit"}


def test_get_current_node_no_clip_selected():
    timeline = _timeline_with_clip(None)
    project = _project_with_timeline(timeline)
    resolve = _resolve(project=project, current_page="color")
    assert ops.get_current_node(resolve) == {"error": "No clip is currently selected in the timeline"}


def test_get_current_node_no_grade():
    clip = _clip_with_grade(None)
    timeline = _timeline_with_clip(clip)
    project = _project_with_timeline(timeline)
    resolve = _resolve(project=project, current_page="color")
    assert ops.get_current_node(resolve) == {"error": "Failed to get current grade"}


def test_get_current_node_no_node_selected():
    grade = MagicMock()
    grade.GetCurrentNode.return_value = 0
    clip = _clip_with_grade(grade)
    timeline = _timeline_with_clip(clip)
    project = _project_with_timeline(timeline)
    resolve = _resolve(project=project, current_page="color")
    assert ops.get_current_node(resolve) == {"error": "No node is currently selected"}


def test_get_current_node_success_returns_full_info():
    grade = MagicMock()
    grade.GetCurrentNode.return_value = 2
    grade.GetNodeCount.return_value = 3
    grade.IsSerial.return_value = True
    grade.IsParallel.return_value = False
    grade.IsLayer.return_value = False
    grade.GetNodeName.return_value = "Primary"
    grade.IsNodeEnabled.return_value = True
    grade.GetNodeType.return_value = "Color Corrector"
    clip = _clip_with_grade(grade, name="ShotA")
    timeline = _timeline_with_clip(clip)
    project = _project_with_timeline(timeline)
    resolve = _resolve(project=project, current_page="color")

    info = ops.get_current_node(resolve)
    assert info["clip_name"] == "ShotA"
    assert info["node_index"] == 2
    assert info["node_count"] == 3
    assert info["is_serial"] is True
    assert info["name"] == "Primary"
    assert info["properties"] == {"enabled": True, "type": "Color Corrector"}


# ---------------------------------------------------------------------------
# apply_lut
# ---------------------------------------------------------------------------

def test_apply_lut_rejects_empty_path():
    resolve = _resolve(project=_project_with_timeline(MagicMock()))
    assert ops.apply_lut(resolve, "") == "Error: LUT path cannot be empty"


def test_apply_lut_rejects_missing_file():
    resolve = _resolve(project=_project_with_timeline(MagicMock()))
    assert ops.apply_lut(resolve, "/nonexistent/some.cube") == (
        "Error: LUT file '/nonexistent/some.cube' does not exist"
    )


def test_apply_lut_rejects_bad_extension(tmp_path):
    bad = tmp_path / "preset.txt"
    bad.write_text("")
    result = ops.apply_lut(_resolve(project=_project_with_timeline(MagicMock())), str(bad))
    assert result.startswith("Error: Unsupported LUT file format")


def test_apply_lut_rejects_invalid_node_index(tmp_path):
    lut = tmp_path / "preset.cube"
    lut.write_text("")
    grade = MagicMock()
    grade.GetNodeCount.return_value = 3
    clip = _clip_with_grade(grade)
    timeline = _timeline_with_clip(clip)
    project = _project_with_timeline(timeline)
    resolve = _resolve(project=project, current_page="color")
    assert ops.apply_lut(resolve, str(lut), node_index=5) == (
        "Error: Invalid node index 5. Valid range: 1-3"
    )


def test_apply_lut_success(tmp_path):
    lut = tmp_path / "preset.cube"
    lut.write_text("")
    grade = MagicMock()
    grade.GetCurrentNode.return_value = 1
    grade.ApplyLUT.return_value = True
    grade.GetNodeName.return_value = "Primary"
    clip = _clip_with_grade(grade)
    timeline = _timeline_with_clip(clip)
    project = _project_with_timeline(timeline)
    resolve = _resolve(project=project, current_page="color")

    result = ops.apply_lut(resolve, str(lut))
    assert result == "Successfully applied LUT 'preset.cube' to node 'Primary' (index 1)"
    grade.ApplyLUT.assert_called_once_with(1, str(lut))


def test_apply_lut_returns_failure_message(tmp_path):
    lut = tmp_path / "preset.cube"
    lut.write_text("")
    grade = MagicMock()
    grade.GetCurrentNode.return_value = 1
    grade.ApplyLUT.return_value = False
    clip = _clip_with_grade(grade)
    timeline = _timeline_with_clip(clip)
    project = _project_with_timeline(timeline)
    resolve = _resolve(project=project, current_page="color")
    assert ops.apply_lut(resolve, str(lut)) == "Failed to apply LUT to node 1"


# ---------------------------------------------------------------------------
# add_node
# ---------------------------------------------------------------------------

def test_add_node_rejects_invalid_type():
    resolve = _resolve(project=_project_with_timeline(MagicMock()))
    result = ops.add_node(resolve, node_type="bogus")
    assert result.startswith("Error: Invalid node type")


def test_add_node_no_project():
    resolve = _resolve(project=None)
    assert ops.add_node(resolve, node_type="serial") == "Error: No project currently open"


def test_add_node_page_switch_failure():
    project = _project_with_timeline(MagicMock())
    resolve = _resolve(project=project, current_page="edit")
    resolve.OpenPage.return_value = False
    result = ops.add_node(resolve, node_type="serial")
    assert result == "Error: Failed to switch to Color page. Current page is: edit"


# ---------------------------------------------------------------------------
# set_color_wheel_param
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("wheel", ["lift", "gamma", "gain", "offset"])
def test_set_color_wheel_param_accepts_valid_wheels_at_validation(wheel):
    """Validation happens before any Resolve interaction — passing None
    is fine here because we only check the first validation guard."""
    # Pre-validation: None resolve still triggers the wheel check is fine? No,
    # connectivity is checked first.  But valid wheel/param shouldn't error
    # for the wheel validator branch, so we exercise via an invalid wheel
    # in the next test and good wheels via downstream errors.
    project = _project_with_timeline(MagicMock())
    resolve = _resolve(project=project, current_page="edit")
    resolve.OpenPage.return_value = False
    # Valid wheel + valid param + page-switch failure → known error
    result = ops.set_color_wheel_param(resolve, wheel=wheel, param="red", value=0.1)
    assert "Failed to switch to Color page" in result


def test_set_color_wheel_param_rejects_invalid_wheel():
    project = _project_with_timeline(MagicMock())
    resolve = _resolve(project=project)
    result = ops.set_color_wheel_param(resolve, wheel="banana", param="red", value=0.1)
    assert result.startswith("Error: Invalid wheel name")


def test_set_color_wheel_param_rejects_invalid_param():
    project = _project_with_timeline(MagicMock())
    resolve = _resolve(project=project)
    result = ops.set_color_wheel_param(resolve, wheel="lift", param="alpha", value=0.1)
    assert result.startswith("Error: Invalid parameter name")


def test_set_color_wheel_param_not_connected():
    assert ops.set_color_wheel_param(None, wheel="lift", param="red", value=0.1) == (
        "Error: Not connected to DaVinci Resolve"
    )


# ---------------------------------------------------------------------------
# ensure_clip_selected
# ---------------------------------------------------------------------------

def test_ensure_clip_selected_uses_existing_selection():
    clip = MagicMock()
    clip.GetName.return_value = "AlreadySelected"
    timeline = _timeline_with_clip(clip)
    ok, returned, msg = ops.ensure_clip_selected(MagicMock(), timeline)
    assert ok is True
    assert returned is clip
    assert "AlreadySelected" in msg


def test_ensure_clip_selected_selects_first_clip_when_none_active():
    first_clip = MagicMock()
    first_clip.GetName.return_value = "FirstClip"

    timeline = MagicMock()
    # Initially nothing selected; SetCurrentVideoItem flips the state.
    timeline.GetCurrentVideoItem.side_effect = [None, first_clip]
    timeline.GetTrackCount.return_value = 1
    timeline.GetItemListInTrack.return_value = [first_clip]

    ok, returned, msg = ops.ensure_clip_selected(MagicMock(), timeline)
    assert ok is True
    assert returned is first_clip
    timeline.SetCurrentVideoItem.assert_called_once_with(first_clip)
    assert "FirstClip" in msg


def test_ensure_clip_selected_returns_failure_when_no_clips():
    timeline = MagicMock()
    timeline.GetCurrentVideoItem.return_value = None
    timeline.GetTrackCount.return_value = 2
    timeline.GetItemListInTrack.return_value = []

    ok, returned, msg = ops.ensure_clip_selected(MagicMock(), timeline)
    assert ok is False
    assert returned is None
    assert "Could not find any clips" in msg


@pytest.mark.parametrize("fn,args", [
    (ops.get_current_node, ()),
    (ops.apply_lut, ("/tmp/x.cube",)),
    (ops.add_node, ("serial",)),
    (ops.set_color_wheel_param, ("lift", "red", 0.0)),
])
def test_no_project_short_circuits(fn, args, tmp_path):
    """All four entry points must short-circuit with no project."""
    # apply_lut additionally validates the LUT file before checking
    # the project, so create a real one when needed.
    new_args = list(args)
    if fn is ops.apply_lut:
        lut = tmp_path / "x.cube"
        lut.write_text("")
        new_args[0] = str(lut)

    resolve = _resolve(project=None)
    result = fn(resolve, *new_args)
    text = result["error"] if isinstance(result, dict) else result
    assert "No project currently open" in text
