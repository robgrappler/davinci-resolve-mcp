"""Unit tests for davinci_resolve_mcp.api.timeline_operations.

Resolve is mocked entirely.  Focused on the simpler entry points that
return strings or small dicts; the larger marker/track helpers are
intentionally out of scope here.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from davinci_resolve_mcp.api import timeline_operations as ops


def _resolve(*, project=None, project_manager=None):
    """Build a MagicMock resolve with the supplied project/project_manager."""
    if project_manager is None:
        project_manager = MagicMock()
        project_manager.GetCurrentProject.return_value = project
    resolve = MagicMock()
    resolve.GetProjectManager.return_value = project_manager
    return resolve, project_manager


def _project_with_timelines(timeline_names, current_timeline_name=None):
    """Build a MagicMock project with the named timelines."""
    project = MagicMock()
    project.GetTimelineCount.return_value = len(timeline_names)

    timelines = []
    for name in timeline_names:
        tl = MagicMock()
        tl.GetName.return_value = name
        timelines.append(tl)

    project.GetTimelineByIndex.side_effect = lambda i: timelines[i - 1] if 1 <= i <= len(timelines) else None

    if current_timeline_name is not None:
        current = next(tl for tl in timelines if tl.GetName() == current_timeline_name)
        project.GetCurrentTimeline.return_value = current
    else:
        project.GetCurrentTimeline.return_value = None

    return project, timelines


# ---------------------------------------------------------------------------
# list_timelines
# ---------------------------------------------------------------------------


def test_list_timelines_not_connected():
    assert ops.list_timelines(None) == ["Error: Not connected to DaVinci Resolve"]


def test_list_timelines_no_project_manager():
    resolve = MagicMock()
    resolve.GetProjectManager.return_value = None
    assert ops.list_timelines(resolve) == ["Error: Failed to get Project Manager"]


def test_list_timelines_no_current_project():
    resolve, _ = _resolve(project=None)
    assert ops.list_timelines(resolve) == ["Error: No project currently open"]


def test_list_timelines_returns_names():
    project, _ = _project_with_timelines(["Main", "B-Roll"])
    resolve, _ = _resolve(project=project)
    assert ops.list_timelines(resolve) == ["Main", "B-Roll"]


def test_list_timelines_empty_returns_info_marker():
    project, _ = _project_with_timelines([])
    resolve, _ = _resolve(project=project)
    assert ops.list_timelines(resolve) == ["No timelines found in the current project"]


# ---------------------------------------------------------------------------
# get_current_timeline_info
# ---------------------------------------------------------------------------


def test_get_current_timeline_info_no_timeline():
    project, _ = _project_with_timelines([])
    resolve, _ = _resolve(project=project)
    assert ops.get_current_timeline_info(resolve) == {"error": "No timeline currently active"}


def test_get_current_timeline_info_returns_metadata():
    project, _ = _project_with_timelines(["Main"], current_timeline_name="Main")
    current = project.GetCurrentTimeline.return_value
    current.GetSetting.side_effect = {
        "timelineFrameRate": "24.000",
        "timelineResolutionWidth": 1920,
        "timelineResolutionHeight": 1080,
    }.get
    current.GetStartTimecode.return_value = "01:00:00:00"

    resolve, _ = _resolve(project=project)
    info = ops.get_current_timeline_info(resolve)
    assert info == {
        "name": "Main",
        "framerate": "24.000",
        "resolution": {"width": 1920, "height": 1080},
        "start_timecode": "01:00:00:00",
    }


# ---------------------------------------------------------------------------
# create_timeline
# ---------------------------------------------------------------------------


def test_create_timeline_rejects_empty_name():
    resolve, _ = _resolve(project=MagicMock())
    assert ops.create_timeline(resolve, "") == "Error: Timeline name cannot be empty"


def test_create_timeline_rejects_duplicate():
    project, _ = _project_with_timelines(["Existing"])
    project.GetMediaPool.return_value = MagicMock()
    resolve, _ = _resolve(project=project)
    assert ops.create_timeline(resolve, "Existing") == "Error: Timeline 'Existing' already exists"


def test_create_timeline_success():
    project, _ = _project_with_timelines([])
    media_pool = MagicMock()
    media_pool.CreateEmptyTimeline.return_value = MagicMock()
    project.GetMediaPool.return_value = media_pool
    resolve, _ = _resolve(project=project)
    assert ops.create_timeline(resolve, "Fresh") == "Successfully created timeline 'Fresh'"
    media_pool.CreateEmptyTimeline.assert_called_once_with("Fresh")


def test_create_timeline_failure():
    project, _ = _project_with_timelines([])
    media_pool = MagicMock()
    media_pool.CreateEmptyTimeline.return_value = None
    project.GetMediaPool.return_value = media_pool
    resolve, _ = _resolve(project=project)
    assert ops.create_timeline(resolve, "Fresh") == "Failed to create timeline 'Fresh'"


def test_create_timeline_no_media_pool():
    project, _ = _project_with_timelines([])
    project.GetMediaPool.return_value = None
    resolve, _ = _resolve(project=project)
    assert ops.create_timeline(resolve, "Fresh") == "Error: Failed to get Media Pool"


# ---------------------------------------------------------------------------
# set_current_timeline
# ---------------------------------------------------------------------------


def test_set_current_timeline_not_found():
    project, _ = _project_with_timelines(["Main"])
    resolve, _ = _resolve(project=project)
    assert ops.set_current_timeline(resolve, "Missing") == "Error: Timeline 'Missing' not found"


def test_set_current_timeline_success():
    project, timelines = _project_with_timelines(["A", "B"])

    # SetCurrentTimeline switches GetCurrentTimeline to point at the target
    def fake_set(tl):
        project.GetCurrentTimeline.return_value = tl
        return True

    project.SetCurrentTimeline.side_effect = fake_set

    resolve, _ = _resolve(project=project)
    assert ops.set_current_timeline(resolve, "B") == "Successfully switched to timeline 'B'"
    project.SetCurrentTimeline.assert_called_once_with(timelines[1])


def test_set_current_timeline_verification_fails():
    project, _ = _project_with_timelines(["A", "B"], current_timeline_name="A")
    # SetCurrentTimeline silently doesn't update GetCurrentTimeline
    project.SetCurrentTimeline.return_value = True
    resolve, _ = _resolve(project=project)
    assert ops.set_current_timeline(resolve, "B") == "Error: Failed to switch to timeline 'B'"


# ---------------------------------------------------------------------------
# delete_timeline
# ---------------------------------------------------------------------------


def test_delete_timeline_not_found():
    project, _ = _project_with_timelines(["Main"])
    resolve, _ = _resolve(project=project)
    assert ops.delete_timeline(resolve, "Missing") == "Error: Timeline 'Missing' not found"


def test_delete_timeline_only_timeline_refused():
    """Deleting the sole timeline (which is also current) must refuse."""
    project, _ = _project_with_timelines(["Only"], current_timeline_name="Only")
    resolve, _ = _resolve(project=project)
    assert (
        ops.delete_timeline(resolve, "Only")
        == "Error: Cannot delete the only timeline in the project. Create a new timeline first."
    )


def test_delete_timeline_switches_off_current_before_deleting():
    project, timelines = _project_with_timelines(["Main", "Backup"], current_timeline_name="Main")
    project.DeleteTimelines.return_value = True
    resolve, _ = _resolve(project=project)

    assert ops.delete_timeline(resolve, "Main") == "Successfully deleted timeline 'Main'"
    # The implementation switches to "Backup" first, then deletes "Main".
    project.SetCurrentTimeline.assert_called_once_with(timelines[1])
    project.DeleteTimelines.assert_called_once_with([timelines[0]])


def test_delete_timeline_failure():
    project, _ = _project_with_timelines(["Main", "Backup"], current_timeline_name="Backup")
    project.DeleteTimelines.return_value = False
    resolve, _ = _resolve(project=project)
    assert ops.delete_timeline(resolve, "Main") == "Failed to delete timeline 'Main'"


# ---------------------------------------------------------------------------
# _frame_to_timecode
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "frame,fps,expected",
    [
        (0, 24.0, "00:00:00:00"),
        (24, 24.0, "00:00:01:00"),
        (3601, 24.0, "00:02:30:01"),  # 3600 frames = 2:30 at 24fps, +1 frame
        (86400, 24.0, "01:00:00:00"),  # 1 hour at 24fps
        (12, 24.0, "00:00:00:12"),
    ],
)
def test_frame_to_timecode(frame, fps, expected):
    assert ops._frame_to_timecode(frame, fps) == expected


# ---------------------------------------------------------------------------
# set_current_frame
# ---------------------------------------------------------------------------


def test_set_current_frame_no_timeline():
    project, _ = _project_with_timelines([])
    resolve, _ = _resolve(project=project)
    assert ops.set_current_frame(resolve, 100) == "Error: No timeline currently active"


def test_set_current_frame_success():
    project, _ = _project_with_timelines(["Main"], current_timeline_name="Main")
    current = project.GetCurrentTimeline.return_value
    current.GetSetting.return_value = "24"
    current.SetCurrentTimecode.return_value = True

    resolve, _ = _resolve(project=project)
    result = ops.set_current_frame(resolve, 48)
    assert result == "Successfully moved playhead to frame 48 (00:00:02:00)"
    current.SetCurrentTimecode.assert_called_once_with("00:00:02:00")


def test_set_current_frame_falls_back_when_setting_missing():
    """When GetSetting returns falsy, the helper falls back to 24 fps."""
    project, _ = _project_with_timelines(["Main"], current_timeline_name="Main")
    current = project.GetCurrentTimeline.return_value
    current.GetSetting.return_value = ""
    current.SetCurrentTimecode.return_value = True

    resolve, _ = _resolve(project=project)
    result = ops.set_current_frame(resolve, 24)
    assert "00:00:01:00" in result


def test_set_current_frame_handles_set_failure():
    project, _ = _project_with_timelines(["Main"], current_timeline_name="Main")
    current = project.GetCurrentTimeline.return_value
    current.GetSetting.return_value = "24"
    current.SetCurrentTimecode.return_value = False

    resolve, _ = _resolve(project=project)
    result = ops.set_current_frame(resolve, 48)
    assert result == "Failed to set current timecode to 00:00:02:00 (Frame 48)"
