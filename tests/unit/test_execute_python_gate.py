"""Regression tests: execute_python must be opt-in via RESOLVE_MCP_ALLOW_EXEC."""

from __future__ import annotations

import importlib
import sys
import types
from unittest.mock import MagicMock


def _build_server(monkeypatch, allow_exec: bool):
    """Build a fresh modular server with the env var toggled."""
    if allow_exec:
        monkeypatch.setenv("RESOLVE_MCP_ALLOW_EXEC", "1")
    else:
        monkeypatch.delenv("RESOLVE_MCP_ALLOW_EXEC", raising=False)

    # Stub the proprietary scripting module before any package import.
    stub = types.ModuleType("DaVinciResolveScript")
    stub.scriptapp = MagicMock(return_value=None)
    monkeypatch.setitem(sys.modules, "DaVinciResolveScript", stub)

    # Drop any cached package modules so the gate is re-evaluated.
    for name in list(sys.modules):
        if name == "davinci_resolve_mcp" or name.startswith("davinci_resolve_mcp."):
            sys.modules.pop(name, None)

    server_mod = importlib.import_module("davinci_resolve_mcp.server")
    return server_mod.create_server()


def _tool_names(server) -> set[str]:
    return set(server._tool_manager._tools.keys())


def test_execute_python_absent_by_default(monkeypatch):
    server = _build_server(monkeypatch, allow_exec=False)
    assert "execute_python" not in _tool_names(server)


def test_execute_python_registered_when_opted_in(monkeypatch):
    server = _build_server(monkeypatch, allow_exec=True)
    assert "execute_python" in _tool_names(server)
