"""Unit tests for davinci_resolve_mcp.api.delivery_operations.

Resolve is mocked entirely.  Focused on the public render-queue helpers
and the small `validate_render_preset` pure helper; the full
`add_to_render_queue` and `ensure_render_settings` flows touch enough
DaVinci state to be more usefully exercised via integration tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from davinci_resolve_mcp.api import delivery_operations as ops


def _resolve(project=None, *, current_page="edit"):
    """Build a MagicMock resolve with the supplied project."""
    pm = MagicMock()
    pm.GetCurrentProject.return_value = project
    resolve = MagicMock()
    resolve.GetProjectManager.return_value = pm
    resolve.GetCurrentPage.return_value = current_page
    return resolve


# ---------------------------------------------------------------------------
# start_render
# ---------------------------------------------------------------------------


def test_start_render_not_connected():
    assert ops.start_render(None) == {"error": "No connection to DaVinci Resolve"}


def test_start_render_no_project_manager():
    resolve = MagicMock()
    resolve.GetProjectManager.return_value = None
    assert ops.start_render(resolve) == {"error": "Failed to get Project Manager"}


def test_start_render_no_current_project():
    resolve = _resolve(project=None)
    assert ops.start_render(resolve) == {"error": "No project is currently open"}


def test_start_render_empty_queue_returns_warning():
    project = MagicMock()
    project.GetRenderJobList.return_value = []
    resolve = _resolve(project=project)
    assert ops.start_render(resolve) == {"warning": "No jobs in render queue", "jobs_count": 0}


def test_start_render_success_uses_modern_api():
    project = MagicMock()
    project.GetRenderJobList.return_value = ["job1", "job2"]
    project.StartRendering.return_value = True
    resolve = _resolve(project=project)
    assert ops.start_render(resolve) == {
        "success": True,
        "message": "Render started successfully",
        "jobs_count": 2,
    }


def test_start_render_falls_back_to_legacy_when_modern_returns_none():
    project = MagicMock()
    project.GetRenderJobList.return_value = ["job1"]
    project.StartRendering.return_value = None
    project.StartRenderingJob.return_value = True
    resolve = _resolve(project=project)
    assert ops.start_render(resolve)["success"] is True
    project.StartRenderingJob.assert_called_once()


def test_start_render_failure_reports_jobs_count():
    project = MagicMock()
    project.GetRenderJobList.return_value = ["a", "b", "c"]
    project.StartRendering.return_value = False
    resolve = _resolve(project=project)
    assert ops.start_render(resolve) == {"error": "Failed to start rendering", "jobs_count": 3}


def test_start_render_switches_to_deliver_page():
    project = MagicMock()
    project.GetRenderJobList.return_value = ["job1"]
    project.StartRendering.return_value = True
    resolve = _resolve(project=project, current_page="edit")
    ops.start_render(resolve)
    resolve.OpenPage.assert_called_with("deliver")


def test_start_render_skips_page_switch_when_already_on_deliver():
    project = MagicMock()
    project.GetRenderJobList.return_value = ["job1"]
    project.StartRendering.return_value = True
    resolve = _resolve(project=project, current_page="deliver")
    ops.start_render(resolve)
    resolve.OpenPage.assert_not_called()


# ---------------------------------------------------------------------------
# get_render_queue_status
# ---------------------------------------------------------------------------


def test_get_render_queue_status_not_connected():
    assert ops.get_render_queue_status(None) == {"error": "No connection to DaVinci Resolve"}


def test_get_render_queue_status_no_project_manager():
    resolve = MagicMock()
    resolve.GetProjectManager.return_value = None
    assert ops.get_render_queue_status(resolve) == {"error": "Failed to get Project Manager"}


# ---------------------------------------------------------------------------
# clear_render_queue
# ---------------------------------------------------------------------------


def test_clear_render_queue_not_connected():
    assert ops.clear_render_queue(None) == {"error": "No connection to DaVinci Resolve"}


def test_clear_render_queue_empty():
    project = MagicMock()
    project.GetRenderJobList.return_value = []
    resolve = _resolve(project=project)
    assert ops.clear_render_queue(resolve) == {
        "success": True,
        "message": "Render queue is already empty",
        "jobs_removed": 0,
    }


def test_clear_render_queue_success():
    project = MagicMock()
    project.GetRenderJobList.return_value = ["job1", "job2"]
    project.GetRenderJobStatus.return_value = "Complete"
    project.DeleteAllRenderJobs.return_value = True
    resolve = _resolve(project=project)
    assert ops.clear_render_queue(resolve) == {
        "success": True,
        "message": "Render queue cleared successfully",
        "jobs_removed": 2,
        "was_rendering": False,
    }


def test_clear_render_queue_stops_rendering_first():
    project = MagicMock()
    project.GetRenderJobList.return_value = ["job1"]
    project.GetRenderJobStatus.return_value = "Rendering"
    project.DeleteAllRenderJobs.return_value = True
    resolve = _resolve(project=project)
    result = ops.clear_render_queue(resolve)
    project.StopRendering.assert_called_once()
    assert result["was_rendering"] is True


def test_clear_render_queue_failure():
    project = MagicMock()
    project.GetRenderJobList.return_value = ["job1"]
    project.GetRenderJobStatus.return_value = "Complete"
    project.DeleteAllRenderJobs.return_value = False
    resolve = _resolve(project=project)
    assert ops.clear_render_queue(resolve) == {
        "error": "Failed to clear render queue",
        "jobs_count": 1,
    }


# ---------------------------------------------------------------------------
# validate_render_preset
# ---------------------------------------------------------------------------


def test_validate_render_preset_found_in_project():
    iface = MagicMock()
    iface.GetRenderPresetList.return_value = ["MyPreset"]
    iface.GetSystemPresetList.return_value = ["YouTube 1080p"]
    valid, presets, msg = ops.validate_render_preset(iface, "MyPreset")
    assert valid is True
    assert "MyPreset" in presets and "YouTube 1080p" in presets
    assert "project" in msg.lower()


def test_validate_render_preset_found_in_system():
    iface = MagicMock()
    iface.GetRenderPresetList.return_value = []
    iface.GetSystemPresetList.return_value = ["YouTube 1080p"]
    valid, presets, msg = ops.validate_render_preset(iface, "YouTube 1080p")
    assert valid is True
    assert presets == ["YouTube 1080p"]
    assert "system" in msg.lower()


def test_validate_render_preset_not_found_lists_available():
    iface = MagicMock()
    iface.GetRenderPresetList.return_value = ["A"]
    iface.GetSystemPresetList.return_value = ["B"]
    valid, presets, msg = ops.validate_render_preset(iface, "C")
    assert valid is False
    assert "not found" in msg
    assert "A" in msg and "B" in msg


def test_validate_render_preset_handles_none_lists():
    """GetRenderPresetList/GetSystemPresetList returning None must not crash."""
    iface = MagicMock()
    iface.GetRenderPresetList.return_value = None
    iface.GetSystemPresetList.return_value = None
    valid, presets, _ = ops.validate_render_preset(iface, "anything")
    assert valid is False
    assert presets == []


@pytest.mark.parametrize(
    "fn",
    [
        ops.start_render,
        ops.get_render_queue_status,
        ops.clear_render_queue,
    ],
)
def test_no_project_short_circuits(fn):
    resolve = _resolve(project=None)
    assert fn(resolve) == {"error": "No project is currently open"}
