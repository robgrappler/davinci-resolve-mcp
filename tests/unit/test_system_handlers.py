from __future__ import annotations

import logging
from typing import Any, Callable, Dict

from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers import system


class StubServer:
    def __init__(self):
        self.resources: Dict[str, Callable[..., Any]] = {}
        self.tools: Dict[str, Callable[..., Any]] = {}

    def resource(self, uri: str):
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.resources[uri] = func
            return func

        return decorator

    def tool(self):
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[func.__name__] = func
            return func

        return decorator


class FakeAdapter:
    def __init__(self, resolve_obj: Any):
        self.resolve_obj = resolve_obj

    def connect(self, *, force: bool = False):
        return self.resolve_obj


class FakeResolve:
    def __init__(self):
        self._page = "edit"

    def GetProductName(self) -> str:
        return "DaVinci Resolve"

    def GetVersionString(self) -> str:
        return "18.5"

    def GetCurrentPage(self) -> str:
        return self._page

    def OpenPage(self, page: str) -> bool:
        self._page = page
        return True


def setup_server():
    fake_resolve = FakeResolve()
    context = ResolveContext(adapter=FakeAdapter(fake_resolve), logger=logging.getLogger("test"))
    server = StubServer()
    system.register(server, context)
    return server, fake_resolve


def test_version_resource_reports_version():
    server, _ = setup_server()
    version = server.resources["resolve://version"]()
    assert "DaVinci Resolve" in version


def test_switch_page_tool_updates_current_page():
    server, fake_resolve = setup_server()
    result = server.tools["switch_page"]("color")
    assert isinstance(result, dict)
    assert result["ok"] is True
    assert result["context"]["page"] == "color"
    assert fake_resolve.GetCurrentPage() == "color"


def test_switch_page_invalid_returns_error():
    server, fake_resolve = setup_server()
    result = server.tools["switch_page"]("bogus")
    assert isinstance(result, dict)
    assert result["ok"] is False
    assert result["error"]["code"] == "INVALID_ARG"
    # Page should not have changed
    assert fake_resolve.GetCurrentPage() == "edit"


def test_debug_environment_returns_envelope():
    server, _ = setup_server()
    result = server.tools["debug_environment"]()
    assert isinstance(result, dict)
    assert result["ok"] is True
    assert "python_version" in result["data"]
    assert "resolve_connected" in result["data"]
