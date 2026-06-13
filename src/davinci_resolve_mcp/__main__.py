"""Console entry point: python -m davinci_resolve_mcp"""

from __future__ import annotations

import argparse
import logging
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="DaVinci Resolve MCP Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    from davinci_resolve_mcp.server import create_server

    server = create_server()
    server.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
