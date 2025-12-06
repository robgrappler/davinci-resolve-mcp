"""Resolve context helpers used by handlers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

from davinci_resolve_mcp.adapters.resolve import ResolveAdapter


@dataclass(slots=True)
class ResolveContext:
    """Shared context passed to handler modules."""

    adapter: ResolveAdapter
    logger: logging.Logger

    def resolve(self) -> Optional[Any]:
        """Return the DaVinci Resolve scripting object, if available."""
        return self.adapter.connect()

    def refresh(self) -> Optional[Any]:
        """Force a reconnection to Resolve."""
        return self.adapter.connect(force=True)
