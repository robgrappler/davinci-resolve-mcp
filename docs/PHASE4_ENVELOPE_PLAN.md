# Phase 4 — Response Envelope Migration (v2.0)

## Decision

Migrate all 93 `@tool()` functions from the current two-shape return format to the
uniform `{ok, data, error, message, context}` envelope defined in
`src/davinci_resolve_mcp/utils/response.py`. Bump the package to v2.0 on completion.

---

## Current state (as of main @ bb12b5a)

### Return shapes in use

| Shape | Description | Files affected |
|---|---|---|
| `str` — `"Error: ..."` / `"Successfully ..."` | Raw string, used by most tools | handlers: app_control, cache, color_presets, delivery, keyframes, layout_presets, projects, system, timeline_items, timelines; api: color_operations, fusion_operations, media_operations, project_operations, timeline_operations |
| `dict` — `{"error": "..."}` / `{"success": True, ...}` | Ad-hoc dict, used by inspection/cloud/project_properties | handlers: cloud, inspection, project_properties, projects; api: color_operations, delivery_operations, timeline_operations |
| `response envelope` (partial) | Only `delivery.py` uses `success_response`/`error_response` | handlers: delivery |

### Tool count per handler file (total: 93)

| File | Tools |
|---|---|
| delivery.py | 12 |
| media_pool.py | 12 |
| timeline_items.py | 7 |
| color_presets.py | 7 |
| cache.py | 7 |
| timelines.py | 7 |
| cloud.py | 6 |
| color.py | 4 |
| app_control.py | 4 |
| projects.py | 5 |
| project_properties.py | 5 |
| layout_presets.py | 5 |
| keyframes.py | 5 |
| fusion.py | 2 |
| inspection.py | 2 |
| system.py | 2 |
| scripting.py | 1 |

---

## Target envelope (already exists in `src/davinci_resolve_mcp/utils/response.py`)

```python
# Success
{"ok": True, "data": Any, "error": None, "message": str|None, "context": dict|None}

# Error
{"ok": False, "data": None, "error": {"code": str, "message": str, "details": Any}, "message": str|None, "context": dict|None}
```

Import: `from davinci_resolve_mcp.utils.response import success_response, error_response`

### Error code conventions (use SCREAMING_SNAKE_CASE)

| Situation | Code |
|---|---|
| Resolve not connected | `NOT_CONNECTED` |
| No project open | `NO_PROJECT` |
| No timeline active | `NO_TIMELINE` |
| Object not found (clip, bin, preset…) | `NOT_FOUND` |
| Invalid argument value | `INVALID_ARG` |
| Operation failed at Resolve API level | `OPERATION_FAILED` |
| Wrong page active | `WRONG_PAGE` |
| Feature unsupported by this Resolve build | `UNSUPPORTED` |

---

## Migration approach

### Per-tool pattern

Before:
```python
@tool()
def set_current_timeline(name: str) -> str:
    if resolve is None:
        return "Error: Not connected to DaVinci Resolve"
    ...
    result = project.SetCurrentTimeline(tl)
    if result:
        return f"Successfully switched to timeline '{name}'"
    else:
        return f"Failed to switch to timeline '{name}'"
```

After:
```python
@tool()
def set_current_timeline(name: str) -> dict:
    if resolve is None:
        return error_response("NOT_CONNECTED", "Not connected to DaVinci Resolve")
    ...
    result = project.SetCurrentTimeline(tl)
    if result:
        return success_response(message=f"Switched to timeline '{name}'", context={"timeline_name": name})
    else:
        return error_response("OPERATION_FAILED", f"Failed to switch to timeline '{name}'")
```

### Rules

1. Return type annotation changes from `str` → `dict` (or `Dict[str, Any]`).
2. Keep `message` field human-readable for LLM display.
3. Put structured data (names, IDs, counts) in `data` or `context`, not embedded in `message`.
4. For functions that currently return rich dicts (e.g. `debug_environment`, `inspect_custom_object`),
 the existing dict payload goes into `data`.
5. The `api/` layer functions are internal and do NOT need to return the envelope themselves.
 However, **`@tool()` handlers that pass api results through directly must wrap them** — the
 public surface must always emit the envelope. Example: `delivery.py` lines like
 `return add_queue_func(resolve, ...)` must become
 `result = add_queue_func(resolve, ...); return success_response(data=result) if result.get("success") else error_response("OPERATION_FAILED", result.get("error", "Unknown error"))`.
 Resources already return typed Python objects (lists, dicts); leave them as-is.

---

## Implementation plan (batched by domain)

Work on branch `claude/phase-4-envelope-migration`. Each batch is one commit. PR at the end.

### Batch 0 — Prep (do first)
- [ ] Extend `response.py` with a `warn_response` helper (same shape as success but `ok=True`,
 `message` describes the soft-no-op). Used for "queue already empty" etc.
- [ ] Update `CHANGELOG.md` with a `## [2.0.0] - Unreleased` header.
- [ ] Add a `test_response_envelope.py` unit test file to confirm the three helpers
 produce the expected shape.

### Batch 1 — `handlers/system.py` + `handlers/app_control.py` (6 tools)
Small files, easy wins. Establish the pattern.

### Batch 2 — `handlers/projects.py` (5 tools)
Medium complexity: multiple early-exits, project-not-found errors.

### Batch 3 — `handlers/timelines.py` (7 tools)
`set_current_timeline`, `create_timeline`, `delete_timeline`, `add_marker`, etc.

### Batch 4 — `handlers/timeline_items.py` (7 tools)
Lots of string returns; straightforward once the pattern is clear.

### Batch 5 — `handlers/media_pool.py` (12 tools)
Largest handler. `list_media_pool_items`, `import_media`, `create_bin`, etc.

### Batch 6 — `handlers/keyframes.py` (5 tools)
String-heavy; consistent pattern.

### Batch 7 — `handlers/color.py` + `handlers/color_presets.py` (11 tools)
`add_node`, `apply_lut`, `set_color_wheel_param`, `copy_grade`, preset CRUD.

### Batch 8 — `handlers/delivery.py` (12 tools)
Partially migrated already. Finish remaining string returns; normalise existing
envelope calls to match error-code conventions.

### Batch 9 — `handlers/cache.py` + `handlers/layout_presets.py` (12 tools)
Similar string-heavy pattern; mechanical.

### Batch 10 — `handlers/cloud.py` + `handlers/project_properties.py` (11 tools)
Currently return ad-hoc dicts. Wrap existing dict payloads into `data`.

### Batch 11 — `handlers/inspection.py` + `handlers/fusion.py` + `handlers/scripting.py` (5 tools)
Small files. `inspect_custom_object` and `object_help` return rich dicts → put in `data`.

### Batch 12 — Version bump + CLAUDE.md update
- [ ] `pyproject.toml`: `version = "2.0.0"`
- [ ] `server.py`: `VERSION = "2.0.0"`
- [ ] `CLAUDE.md`: replace "Error shape" section with envelope docs and example parsing snippet
- [ ] `CHANGELOG.md`: fill in the release date for `[2.0.0]`
- [ ] `test_tool_parity.py`: assert all tools return `dict` with `"ok"` key (spot-check via
 calling each tool on mock resolve and checking `isinstance(result, dict) and "ok" in result`)

---

## CLAUDE.md "Error shape" replacement

Replace the existing "Error shape — two formats exist" section with:

```markdown
## Response envelope

All tools return a uniform dict:

```python
{
    "ok": bool,           # True = success, False = failure
    "data": Any,          # Payload on success; None on error
    "error": {            # None on success; present on error
        "code": str,      # Machine-readable e.g. "NOT_CONNECTED"
        "message": str,   # Human-readable description
        "details": Any    # Raw API result or exception string, if available
    },
    "message": str | None, # Human-readable summary (present when passed; may be absent)
    "context": dict | None # Extra metadata e.g. {"project_name": "..."} (may be absent)
}
```

**Checking success:**
```python
result = call_tool(...)
if not result["ok"]:
    print(result["error"]["code"], result["error"]["message"])
else:
    data = result["data"]
    msg = result.get("message")   # use .get() — field is optional
```

**Common error codes:** `NOT_CONNECTED`, `NO_PROJECT`, `NO_TIMELINE`, `NOT_FOUND`,
`INVALID_ARG`, `OPERATION_FAILED`, `WRONG_PAGE`, `UNSUPPORTED`.
```

---

## Testing strategy

1. Each batch: run `python -m pytest tests/unit/ -q` after the commit. **Existing handler tests
   that assert string content (e.g. `"Successfully switched" in result`) WILL break** when those
   tools are migrated — update them in the same commit as the tool migration. New assertion pattern:
   `assert result["ok"] is True` / `assert result["error"]["code"] == "NOT_CONNECTED"`.
2. Batch 0: new `test_response_envelope.py` adds ≥6 tests.
3. Batch 12: new spot-check test in `test_tool_parity.py` validates envelope shape on sampled tools.
4. Final: `ruff check src/ tests/unit/ && ruff format --check src/ tests/unit/` must pass.

---

## Handoff protocol

### State a new agent must reconstruct

1. **Repo**: `robgrappler/davinci-resolve-mcp`
2. **Working branch**: `claude/phase-4-envelope-migration` (create from main if it doesn't exist yet)
3. **What's done**: Phases 0–3 complete and merged (PRs #9–12 on main). The last task is this envelope migration.
4. **Plan file**: `docs/PHASE4_ENVELOPE_PLAN.md` (this file). Check the batch checkboxes to see progress.
5. **Test command**: `python -m pytest tests/unit/ -q` (must always return 207 passed, growing as batches add tests).
6. **Lint command**: `ruff check src/ tests/unit/ && ruff format --check src/ tests/unit/`

### Steps for a new agent to continue

```
1. git fetch origin main && git checkout claude/phase-4-envelope-migration
 # or: git checkout -b claude/phase-4-envelope-migration origin/main (if branch doesn't exist)

2. Read docs/PHASE4_ENVELOPE_PLAN.md — find the first unchecked [ ] batch.

3. Read src/davinci_resolve_mcp/utils/response.py to understand the helpers.

4. Read one already-migrated handler (delivery.py is the reference, partially done)
 to see the pattern in practice.

5. Implement the unchecked batch. Check the box in this file when done.

6. Run tests + lint. Fix any failures.

7. Commit with message: "phase 4 batch N: migrate <handler>.py to envelope"

8. Repeat from step 2 until all batches are done.

9. Open PR against main with title: "Phase 4: uniform response envelope + v2.0.0 bump"
```
