"""Regression tests: execute_python must be opt-in via RESOLVE_MCP_ALLOW_EXEC."""

from __future__ import annotations

import asyncio
import importlib
import sys
from unittest.mock import MagicMock


def _import_server(monkeypatch, allow_exec: bool):
    """Import a fresh copy of the monolithic server module."""
    if allow_exec:
        monkeypatch.setenv("RESOLVE_MCP_ALLOW_EXEC", "1")
    else:
        monkeypatch.delenv("RESOLVE_MCP_ALLOW_EXEC", raising=False)

    # Avoid importing the real Resolve scripting module during tests.
    monkeypatch.setitem(sys.modules, "DaVinciResolveScript", MagicMock())
    sys.modules.pop("resolve_mcp_server", None)
    return importlib.import_module("resolve_mcp_server")


def _tool_names(module) -> set[str]:
    return {tool.name for tool in asyncio.run(module.mcp.list_tools())}


def test_execute_python_absent_by_default(monkeypatch):
    module = _import_server(monkeypatch, allow_exec=False)
    assert "execute_python" not in _tool_names(module)


def test_execute_python_registered_when_opted_in(monkeypatch):
    module = _import_server(monkeypatch, allow_exec=True)
    assert "execute_python" in _tool_names(module)
