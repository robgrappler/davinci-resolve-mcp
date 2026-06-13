"""Unit tests for davinci_resolve_mcp.api.project_operations.

Resolve is mocked entirely — these tests pin the current behavior of
each function so the upcoming response-envelope migration can change
output shape with confidence.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from davinci_resolve_mcp.api import project_operations as ops


def _resolve_with_projects(project_names, current_project=None):
    """Build a MagicMock resolve whose project manager lists the given names."""
    pm = MagicMock()
    pm.GetProjectListInCurrentFolder.return_value = list(project_names)
    pm.GetCurrentProject.return_value = current_project
    resolve = MagicMock()
    resolve.GetProjectManager.return_value = pm
    return resolve, pm


# ---------------------------------------------------------------------------
# list_projects
# ---------------------------------------------------------------------------

def test_list_projects_not_connected():
    assert ops.list_projects(None) == ["Error: Not connected to DaVinci Resolve"]


def test_list_projects_no_project_manager():
    resolve = MagicMock()
    resolve.GetProjectManager.return_value = None
    assert ops.list_projects(resolve) == ["Error: Failed to get Project Manager"]


def test_list_projects_filters_empty_names():
    resolve, _ = _resolve_with_projects(["Alpha", "", "Beta", None])
    assert ops.list_projects(resolve) == ["Alpha", "Beta"]


# ---------------------------------------------------------------------------
# get_current_project_name
# ---------------------------------------------------------------------------

def test_get_current_project_name_not_connected():
    assert ops.get_current_project_name(None) == "Error: Not connected to DaVinci Resolve"


def test_get_current_project_name_no_project():
    resolve, _ = _resolve_with_projects([], current_project=None)
    assert ops.get_current_project_name(resolve) == "No project currently open"


def test_get_current_project_name_returns_name():
    project = MagicMock()
    project.GetName.return_value = "Demo Reel"
    resolve, _ = _resolve_with_projects(["Demo Reel"], current_project=project)
    assert ops.get_current_project_name(resolve) == "Demo Reel"


# ---------------------------------------------------------------------------
# open_project
# ---------------------------------------------------------------------------

def test_open_project_rejects_empty_name():
    resolve, _ = _resolve_with_projects(["A"])
    assert ops.open_project(resolve, "") == "Error: Project name cannot be empty"


def test_open_project_not_found_lists_available():
    resolve, _ = _resolve_with_projects(["Alpha", "Beta"])
    result = ops.open_project(resolve, "Gamma")
    assert "not found" in result
    assert "Alpha" in result and "Beta" in result


def test_open_project_load_success():
    resolve, pm = _resolve_with_projects(["Alpha"])
    pm.LoadProject.return_value = True
    assert ops.open_project(resolve, "Alpha") == "Successfully opened project 'Alpha'"
    pm.LoadProject.assert_called_once_with("Alpha")


def test_open_project_load_failure_reports_failure():
    resolve, pm = _resolve_with_projects(["Alpha"])
    pm.LoadProject.return_value = False
    assert ops.open_project(resolve, "Alpha") == "Failed to open project 'Alpha'"


# ---------------------------------------------------------------------------
# create_project
# ---------------------------------------------------------------------------

def test_create_project_rejects_empty_name():
    resolve, _ = _resolve_with_projects([])
    assert ops.create_project(resolve, "") == "Error: Project name cannot be empty"


def test_create_project_rejects_duplicate_name():
    resolve, _ = _resolve_with_projects(["Existing"])
    assert ops.create_project(resolve, "Existing") == "Error: Project 'Existing' already exists"


def test_create_project_success():
    resolve, pm = _resolve_with_projects([])
    pm.CreateProject.return_value = True
    assert ops.create_project(resolve, "NewProj") == "Successfully created project 'NewProj'"
    pm.CreateProject.assert_called_once_with("NewProj")


def test_create_project_failure_reports_failure():
    resolve, pm = _resolve_with_projects([])
    pm.CreateProject.return_value = False
    assert ops.create_project(resolve, "NewProj") == "Failed to create project 'NewProj'"


# ---------------------------------------------------------------------------
# save_project
# ---------------------------------------------------------------------------

def test_save_project_not_connected():
    assert ops.save_project(None) == "Error: Not connected to DaVinci Resolve"


def test_save_project_no_current_project():
    resolve, _ = _resolve_with_projects([], current_project=None)
    assert ops.save_project(resolve) == "Error: No project currently open"


def test_save_project_reports_autosave_when_media_pool_present():
    project = MagicMock()
    project.GetName.return_value = "Active"
    project.GetMediaPool.return_value = MagicMock()
    resolve, _ = _resolve_with_projects(["Active"], current_project=project)
    result = ops.save_project(resolve)
    assert "Active" in result and "auto-save" in result


def test_save_project_handles_missing_media_pool():
    project = MagicMock()
    project.GetMediaPool.return_value = None
    resolve, _ = _resolve_with_projects(["Active"], current_project=project)
    assert ops.save_project(resolve) == "Project is likely already saved (auto-save enabled)"


@pytest.mark.parametrize("fn", [
    ops.list_projects,
    ops.get_current_project_name,
    ops.save_project,
])
def test_no_project_manager_branch(fn):
    """Each top-level function must short-circuit when GetProjectManager fails."""
    resolve = MagicMock()
    resolve.GetProjectManager.return_value = None
    result = fn(resolve)
    text = result[0] if isinstance(result, list) else result
    assert "Project Manager" in text
