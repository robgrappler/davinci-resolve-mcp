# Repository Audit & Improvement Roadmap

*Audited: June 2026, at v1.3.8.*

This document records a full audit of the repository and lays out a phased
improvement plan. Phase 0 (quick wins) was implemented alongside this
document; later phases are intended to land as separate, incremental PRs.

## Summary of findings

### Critical

1. **`execute_python` arbitrary code execution** (`src/resolve_mcp_server.py`).
   The tool passed client-supplied strings to `exec()` with the server
   module's globals, with no gating. MCP tools are invoked by LLMs that
   ingest untrusted content (clip names, markers, transcripts), so a prompt
   injection could reach `exec()`.
   **Fixed in Phase 0:** disabled unless `RESOLVE_MCP_ALLOW_EXEC=1`; runs in
   an isolated namespace; documented in the README Security section.

2. **Broken quick-start symlinks.** Root `run-now.sh` / `run-now.bat` were
   absolute symlinks into a maintainer's home directory
   (`/Users/samuelgursky/...`), so the documented quick start failed for
   every user. **Fixed in Phase 0:** replaced with portable wrappers that
   delegate to `scripts/run-now.{sh,bat}`.

### Architecture

3. **Two parallel server implementations.**
   - *Live:* the monolithic `src/resolve_mcp_server.py` (~4,900 lines,
     131 `@mcp.tool`/`@mcp.resource` registrations), entered via
     `src/main.py`. Connects to Resolve at import time via a module-level
     global.
   - *Dormant:* the modular `src/davinci_resolve_mcp/` package — a
     `create_server()` bootstrap, a lazy-connecting `ResolveAdapter`
     (`adapters/resolve.py`), a `ResolveContext`, a `HandlerRegistry`
     pattern (`handlers/registry.py`), and 15 domain handler modules with
     122 registrations. It is currently dead code: `src/main.py` never
     imports it.

   Verified parity gap (extracted from both implementations):
   - **Monolith-only (10):** `add_fusion_effect`, `add_fusion_generator`,
     `add_to_render_queue_json`, `create_timeline_from_clips`,
     `debug_environment`, `execute_python`, `get_timeline_items_resource`
     (resource), `list_media_pool_items`, `razor_timeline`,
     `set_current_frame`.
   - **Modular-only (1):** `set_timeline_item_name`.

   All monolith-only tools are thin wrappers over `src/api/*` functions,
   which the modular handlers already import — so `src/api/` is the shared
   operations layer, and the port is mechanical.

4. **`src/api/` overlap.** ~4,100 lines across six modules
   (`media_operations.py`, `color_operations.py`, `timeline_operations.py`,
   `delivery_operations.py`, `fusion_operations.py`,
   `project_operations.py`) serve both implementations.

### Code quality

5. **35 bare `except:` clauses** across `src/api/`, `src/utils/`, and
   handlers (worst offenders: `api/color_operations.py`,
   `api/timeline_operations.py`, `utils/object_inspection.py`). These
   swallow real errors and make debugging impossible.
6. **Module-level `sys.path` manipulation** in `src/main.py`,
   `src/resolve_mcp_server.py`, and `src/utils/platform.py` — a consequence
   of the project not being pip-installable.
7. **Import-time connection:** `resolve = get_resolve()` runs when
   `resolve_mcp_server.py` is imported. The modular package's
   `ResolveAdapter` already solves this with lazy connection + caching.
8. **Inconsistent error formats:** some tools return `"Error: ..."` strings,
   others `{"error": ...}` dicts, even though `src/utils/response.py`
   defines a canonical `{ok, data, error, message, context}` envelope that
   is barely used.
9. **Hardcoded platform paths** in `src/utils/platform.py`; the Linux paths
   (`/opt/resolve/...`) are unverified and the README declares Linux
   unsupported.

### Infrastructure

10. **No packaging.** No `pyproject.toml`/`setup.py`; not pip-installable.
    `requirements.txt` was unpinned and contained a redundant
    `git+https://...python-sdk.git` line (`mcp[cli]` on PyPI *is* that SDK)
    plus dev-only deps (`requests`, `psutil`, `jsonrpcserver`) presented as
    runtime deps. **Partially fixed in Phase 0** (git dep removed, dev deps
    annotated); full fix is Phase 1.
11. **Hardcoded user paths** in `scripts/run-server.sh` (`/Users/ppt04/...`)
    and `examples/media/import_folder.py`. **Fixed in Phase 0.**
12. **Stale duplicate** `scripts/resolve_mcp_server.py` (out of date copy of
    the real server). **Removed in Phase 0.**
13. **Three changelogs** (root `CHANGELOG.md`, root `CHANGES.md`,
    `docs/CHANGELOG.md`) with overlapping content. **Consolidated in
    Phase 0** into a single root `CHANGELOG.md`.
14. **Conflicting Python version claims** (README 3.6+, INSTALL 3.9+, CI
    3.11; the MCP SDK actually requires ≥3.10). **Aligned to 3.10+ in
    Phase 0.**
15. **Script sprawl:** ~26 files in `scripts/` with heavily overlapping
    launchers (`launch.sh`, `mcp_resolve_launcher.sh`, `server.sh`,
    `run-now.*`, `run-server.sh`, `restart-server.*`,
    `mcp_resolve-{claude,cursor}_start`, multiple installers).
16. **Thin CI:** a single ubuntu-only workflow running pytest; no linting,
    no type checking, no multi-OS coverage despite the project targeting
    macOS/Windows.
17. **Thin unit tests:** only three small mock-based test files in
    `tests/unit/`; everything else under `tests/` requires a live DaVinci
    Resolve instance.

## Roadmap

The agreed direction is to **converge on the modular
`src/davinci_resolve_mcp/` package and retire the monolith**.

### Phase 0 — Hygiene quick wins (done, this PR)

- Gate `execute_python` behind `RESOLVE_MCP_ALLOW_EXEC=1`; isolate its exec
  namespace; add README Security section; add a regression test.
- Replace broken root symlinks with portable wrapper scripts.
- Remove stale `scripts/resolve_mcp_server.py` and the duplicate import in
  `src/resolve_mcp_server.py`.
- Clean `requirements.txt`; fix hardcoded paths in `scripts/run-server.sh`
  and `examples/media/import_folder.py`.
- Consolidate the three changelogs; align Python version claims to 3.10+.

### Phase 1 — Packaging + CI (effort: M, risk: low)

- Add `pyproject.toml`: `requires-python = ">=3.10"`, runtime dependency
  `mcp[cli]` only, dev extras (`pytest`, `ruff`, `requests`, `psutil`,
  `jsonrpcserver`), ruff + pytest configuration.
- CI: add `ruff check` / `ruff format --check`; matrix
  `{ubuntu, macos, windows} × {3.10, 3.12}`; install via
  `pip install -e .[dev]` so packaging is validated on every run; coverage
  reporting with a modest floor.

### Phase 2 — Convergence on the modular package (effort: M, user-visible)

1. **Parity test first:** add `tests/unit/test_tool_parity.py` that builds
   the server via `create_server()` with a stubbed connector (pattern
   already in `tests/unit/test_resolve_adapter.py`) and compares registered
   tool/resource names against a frozen manifest generated from the
   monolith's 131 names. This permanently guards against tool loss.
2. **Port the 9 missing tools** into handlers:
   - `add_fusion_effect`, `add_fusion_generator` → new
     `handlers/fusion.py` (wrapping `src/api/fusion_operations.py`)
   - `add_to_render_queue_json` → `handlers/delivery.py`, using
     `src/utils/response.py` envelopes
   - `razor_timeline`, `set_current_frame`, `create_timeline_from_clips`,
     `get_timeline_items_resource` → `handlers/timelines.py`
   - `list_media_pool_items` → `handlers/media_pool.py`
   - `debug_environment` → `handlers/system.py`
   - `execute_python` → gated `handlers/scripting.py`
3. **Flip the entry point:** add `davinci_resolve_mcp/__main__.py` and a
   `davinci-resolve-mcp` console script; keep `src/main.py` as a
   compatibility shim; update `config/` templates to
   `python -m davinci_resolve_mcp`.

### Phase 3 — Dead-code removal (effort: M, after Phase 2 soaks)

- Delete `src/resolve_mcp_server.py` and the root shim.
- Move `src/api` → `davinci_resolve_mcp/api` and `src/utils` →
  `davinci_resolve_mcp/utils`; rewrite imports; remove all `sys.path`
  hacks (and the `tests/conftest.py` path shim, once `pip install -e .`
  covers it).
- Prune `scripts/` from ~26 files to ~4 (pre-flight check + setup); the
  console script replaces all launch wrappers.

### Phase 4 — Quality ratchet (ongoing)

- Convert bare `except:` to `except Exception` with logging; enforce via
  ruff rule `E722`.
- Migrate tool returns to the `src/utils/response.py` envelope
  domain-by-domain (this changes tool output shape — version-bump and
  changelog each batch).
- Grow unit tests around `src/api` operations with a mocked Resolve object.
- Verify the Linux paths in `utils/platform.py` against a real install or
  explicitly drop the Linux branch.
