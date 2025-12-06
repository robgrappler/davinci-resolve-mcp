"""Adapter for interacting with the DaVinci Resolve scripting API."""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

from src.utils.platform import get_platform, get_resolve_paths, setup_environment
from src.utils.resolve_connection import initialize_resolve

Connector = Callable[[], Optional[Any]]


class ResolveAdapter:
    """Lazily establishes and caches a Resolve scripting connection."""

    def __init__(
        self,
        *,
        logger: Optional[logging.Logger] = None,
        connector: Optional[Connector] = None,
    ) -> None:
        self._logger = logger or logging.getLogger("davinci-resolve-mcp.adapter")
        self._connector = connector or initialize_resolve
        self._resolve: Optional[Any] = None
        self._environment_ready = False
        self._paths = get_resolve_paths()
        self._platform = get_platform()

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def platform(self) -> str:
        """Return the detected platform identifier."""
        return self._platform

    @property
    def paths(self) -> dict[str, str]:
        """Return a copy of the Resolve scripting paths."""
        return dict(self._paths)

    def connect(self, *, force: bool = False) -> Optional[Any]:
        """Return a Resolve connection, establishing one if needed."""
        if not force and self._resolve is not None:
            return self._resolve

        self._ensure_environment()

        try:
            resolve = self._connector()
        except Exception as exc:  # pragma: no cover - defensive logging
            self._logger.exception("Unexpected error while connecting to Resolve: %s", exc)
            resolve = None

        if resolve is None:
            self._logger.warning("DaVinci Resolve is not available on %s", self._platform)
        else:
            self._logger.info(
                "Connected to DaVinci Resolve: %s %s",
                getattr(resolve, "GetProductName", lambda: "Unknown")(),
                getattr(resolve, "GetVersionString", lambda: "Unknown")(),
            )

        self._resolve = resolve
        return self._resolve

    def disconnect(self) -> None:
        """Clear the cached Resolve connection."""
        self._resolve = None

    def _ensure_environment(self) -> None:
        if self._environment_ready:
            return

        if setup_environment():
            self._environment_ready = True
            self._logger.debug("Configured Resolve environment paths: %s", self._paths)
        else:  # pragma: no cover - setup failure just logs
            self._logger.warning(
                "Failed to automatically configure Resolve environment. Paths: %s",
                self._paths,
            )
