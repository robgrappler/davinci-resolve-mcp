from __future__ import annotations

from davinci_resolve_mcp.utils.response import error_response, success_response, warn_response


def test_success_response_minimal_shape() -> None:
    result = success_response()

    assert result == {
        "ok": True,
        "data": None,
        "error": None,
    }


def test_success_response_with_payload_message_and_context() -> None:
    result = success_response(
        data={"id": "clip-1"},
        message="Imported media",
        context={"clip_name": "take_01.mov"},
    )

    assert result["ok"] is True
    assert result["data"] == {"id": "clip-1"}
    assert result["error"] is None
    assert result["message"] == "Imported media"
    assert result["context"] == {"clip_name": "take_01.mov"}


def test_error_response_minimal_shape() -> None:
    result = error_response("NOT_CONNECTED", "Not connected to DaVinci Resolve")

    assert result == {
        "ok": False,
        "data": None,
        "error": {
            "code": "NOT_CONNECTED",
            "message": "Not connected to DaVinci Resolve",
        },
    }


def test_error_response_with_details_and_context() -> None:
    result = error_response(
        "OPERATION_FAILED",
        "Failed to create timeline",
        details={"raw": False},
        context={"timeline_name": "Scene 1"},
    )

    assert result["ok"] is False
    assert result["data"] is None
    assert result["error"] == {
        "code": "OPERATION_FAILED",
        "message": "Failed to create timeline",
        "details": {"raw": False},
    }
    assert result["context"] == {"timeline_name": "Scene 1"}


def test_warn_response_minimal_shape() -> None:
    result = warn_response("Render queue is already empty")

    assert result == {
        "ok": True,
        "data": None,
        "error": None,
        "message": "Render queue is already empty",
    }


def test_warn_response_with_payload_and_context() -> None:
    result = warn_response(
        "Project already open",
        data={"project_name": "Demo"},
        context={"requested_project": "Demo"},
    )

    assert result["ok"] is True
    assert result["data"] == {"project_name": "Demo"}
    assert result["error"] is None
    assert result["message"] == "Project already open"
    assert result["context"] == {"requested_project": "Demo"}
