"""Test configuration for ensuring project modules are importable.

Both paths are needed: src/ so `davinci_resolve_mcp` resolves, and the
repo root so the `from src.utils...` / `from src.api...` imports used
inside the package resolve (mirroring how src/main.py runs the server).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

for path in (SRC_DIR, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
