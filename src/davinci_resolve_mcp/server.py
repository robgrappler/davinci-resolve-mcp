"""Server bootstrap for the DaVinci Resolve MCP service."""

from __future__ import annotations

import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP

from davinci_resolve_mcp.adapters.resolve import ResolveAdapter
from davinci_resolve_mcp.context import ResolveContext
from davinci_resolve_mcp.handlers import register_all

VERSION = "2.0.0"


def create_server(*, logger: Optional[logging.Logger] = None) -> FastMCP:
    """Create and configure the FastMCP server instance."""
    logger = logger or logging.getLogger("davinci-resolve-mcp")
    adapter = ResolveAdapter(logger=logger)
    context = ResolveContext(adapter=adapter, logger=logger)

    logger.info("Starting DaVinci Resolve MCP Server v%s", VERSION)
    logger.info("Detected platform: %s", adapter.platform)
    paths = adapter.paths
    logger.info("Resolve API path: %s", paths.get("api_path"))
    logger.info("Resolve library path: %s", paths.get("lib_path"))

    server = FastMCP("DaVinciResolveMCP")
    register_all(server, context)

    # Attempt an eager connection so availability is logged up front.
    adapter.connect()

    return server
