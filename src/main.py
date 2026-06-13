#!/usr/bin/env python3
"""DaVinci Resolve MCP Server - Main Entry Point

Legacy compatibility shim: delegates to the modular davinci_resolve_mcp
package.  New callers should use ``python -m davinci_resolve_mcp`` or
the ``davinci-resolve-mcp`` console script instead.
"""

import sys
from pathlib import Path

# Ensure the repo root is on sys.path so ``from src.…`` imports work
# inside the handler modules (they haven't been moved into the package yet).
project_dir = Path(__file__).parent.parent
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from davinci_resolve_mcp.__main__ import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
