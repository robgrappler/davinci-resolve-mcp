#!/usr/bin/env python3
"""Common response helpers for MCP tools.

These helpers provide a stable, pipeline‑friendly envelope so callers can
rely on a consistent structure:

{
  "ok": bool,
  "data": Any | None,
  "error": {"code": str, "message": str, "details": Any} | None,
  "message": str | None,
  "context": dict | None,
}
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Standard success envelope.

    Args:
        data: Optional payload
        message: Optional human‑readable summary
        context: Optional extra context (match id, project name, etc.)
    """

    resp: Dict[str, Any] = {
        "ok": True,
        "data": data,
        "error": None,
    }
    if message is not None:
        resp["message"] = message
    if context is not None:
        resp["context"] = context
    return resp


def error_response(
    code: str,
    message: str,
    *,
    details: Any = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Standard error envelope.

    Args:
        code: Stable, machine‑readable error code (e.g. "NOT_CONNECTED")
        message: Human‑readable message
        details: Optional raw result / exception / extra fields
        context: Optional extra context (match id, project name, etc.)
    """

    err: Dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if details is not None:
        err["details"] = details

    resp: Dict[str, Any] = {
        "ok": False,
        "data": None,
        "error": err,
    }
    if context is not None:
        resp["context"] = context
    return resp
