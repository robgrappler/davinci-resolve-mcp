"""Test configuration: ensure the davinci_resolve_mcp package is importable.

After Phase 3 the package lives under src/davinci_resolve_mcp/.  Tests rely
on the editable install (``pip install -e .``) wiring up the package, but
the path is also added here so the suite works when run without an install.
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
