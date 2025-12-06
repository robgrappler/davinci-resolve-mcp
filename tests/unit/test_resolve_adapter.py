from __future__ import annotations

import logging

from davinci_resolve_mcp.adapters.resolve import ResolveAdapter


class StubConnector:
    def __init__(self, result):
        self._result = result
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return self._result


def test_connect_caches_connection():
    stub = StubConnector(object())
    adapter = ResolveAdapter(logger=logging.getLogger("test"), connector=stub)

    first = adapter.connect()
    second = adapter.connect()

    assert first is second
    assert stub.calls == 1

    adapter.connect(force=True)
    assert stub.calls == 2


def test_connect_handles_missing_resolve():
    stub = StubConnector(None)
    adapter = ResolveAdapter(logger=logging.getLogger("test"), connector=stub)

    assert adapter.connect() is None
    assert stub.calls == 1
