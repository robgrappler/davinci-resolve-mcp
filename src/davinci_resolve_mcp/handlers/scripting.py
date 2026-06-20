"""Optional handler for execute_python — gated behind RESOLVE_MCP_ALLOW_EXEC=1."""

from __future__ import annotations

import logging
import os
import traceback
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers.registry import HandlerRegistry, install_handlers
from davinci_resolve_mcp.utils.response import success_response, error_response

logger = logging.getLogger("davinci-resolve-mcp.scripting")
registry = HandlerRegistry()
tool = registry.tool
resolve: Optional[Any] = None

_ENABLED = os.environ.get("RESOLVE_MCP_ALLOW_EXEC") == "1"

if _ENABLED:
    logger.warning(
        "RESOLVE_MCP_ALLOW_EXEC=1: the execute_python tool is enabled. "
        "Any MCP client can run arbitrary Python code on this machine."
    )

    @tool()
    def execute_python(code: str) -> Dict[str, Any]:
        """Execute arbitrary Python code in DaVinci Resolve context.

        Args:
            code: The Python code to execute
        """
        if resolve is None:
            return error_response(
                "NOT_CONNECTED",
                "Could not connect to DaVinci Resolve. Ensure the application is running and the MCP API is enabled in preferences.",
            )

        try:
            exec_scope: dict[str, Any] = {"resolve": resolve}

            project_manager = resolve.GetProjectManager()
            if project_manager:
                exec_scope["project_manager"] = project_manager
                current_project = project_manager.GetCurrentProject()
                if current_project:
                    exec_scope["project"] = current_project
                    exec_scope["media_pool"] = current_project.GetMediaPool()
                    exec_scope["timeline"] = current_project.GetCurrentTimeline()

            exec(code, exec_scope)

            if "result" in exec_scope:
                raw = exec_scope["result"]
                try:
                    import json

                    json.dumps(raw)
                    safe = raw
                except (TypeError, ValueError):
                    safe = str(raw)
                return success_response({"result": safe}, message="Executed successfully")
            return success_response({"result": None}, message="Executed successfully (no 'result' variable set)")

        except Exception as e:
            return error_response(
                "OPERATION_FAILED",
                f"Error executing Python code: {str(e)}",
                details={"traceback": traceback.format_exc()},
            )


def register(server: FastMCP, context: ResolveContext) -> None:
    """Register handlers defined in this module (only if RESOLVE_MCP_ALLOW_EXEC=1)."""
    if _ENABLED:
        install_handlers(server, context, registry, globals())
