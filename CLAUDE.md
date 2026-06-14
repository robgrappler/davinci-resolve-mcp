# CLAUDE.md — AI Agent Guide for DaVinci Resolve MCP

This file is read automatically by Claude Code at session start.  Any other
LLM-based agent should read it before using any tool.

---

## What this server does

This MCP server bridges AI agents to **DaVinci Resolve** (professional video
editing / colour grading software by Blackmagic Design) via Resolve's Python
scripting API.  The server exposes **92 tools** and **32 resources** that
cover every major Resolve domain: projects, timelines, media pool, colour,
delivery, Fusion, and system control.

The server is a thin coordination layer — it never stores state of its own.
Every call goes live to the running Resolve process and reflects the current
UI state.

---

## Hard prerequisites — check these first

Before calling any tool:

1. **DaVinci Resolve must be running** on the same machine as the server.
   Nothing will work if Resolve is closed.  Read the resource
   `resolve://version` as a connectivity probe.

2. **A project must be open** in Resolve for the vast majority of tools.
   `resolve://projects` (resource) and `open_project` are the only calls that
   work without a currently open project.  Every other call that touches a
   timeline, media pool, colour grade, or render queue will fail with
   `"No project currently open"` if called when Resolve is on the Project
   Manager screen.

3. **A timeline must be active** for timeline-scoped tools (`set_current_frame`,
   `add_marker`, `razor_timeline`, `list_timeline_clips`, timeline item tools,
   colour tools).  Confirm with the resource `resolve://current-timeline`
   before using these tools.

4. **The correct Resolve page must be active** for page-gated tools (see
   below).  Resolve's scripting API silently ignores or errors on operations
   attempted from the wrong page.

---

## Page model — the most important concept

DaVinci Resolve is divided into **pages**, each with a separate tool set.
Several tools will return an error like `"Not on Color page"` if called while
the wrong page is active.  Always navigate first.

| Page name (string) | Access via |
|---|---|
| `"media"` | Media Pool — import, organise, transcribe |
| `"edit"` | Edit / Cut — timeline clips, markers, razor |
| `"color"` | Colour — grades, nodes, LUTs, wheels |
| `"fusion"` | Fusion — VFX composition |
| `"fairlight"` | Fairlight — audio mixing |
| `"deliver"` | Deliver — render queue, export |

**How to navigate:**
```
switch_page(page="color")   # navigate before colour tools
switch_page(page="deliver") # navigate before render tools
```

**How to check current page:**
```
resolve://current-page      # returns e.g. "edit"
```

Color tools (`apply_lut`, `set_color_wheel_param`, `add_node`, `copy_grade`,
`apply_color_preset`, `save_color_preset`) **require the Color page**.
The resource `resolve://color/current-node` also reads from the Color page.
The handlers do attempt an auto-switch, but an explicit `switch_page` call before
a batch of colour operations is cleaner and more reliable.

Render/delivery tools (`add_to_render_queue`, `start_render`) **require the
Deliver page**.  The resource `resolve://delivery/render-queue/status` also
reads from the Deliver page.

Fusion tools (`add_fusion_effect`, `add_fusion_generator`) operate on timeline
items by ID and do not require a page switch, but Resolve must be in Fusion page
or Edit page for the comp to be accessible.

---

## Error shape — two formats exist

Tools return errors in two shapes depending on the domain.  Always check for
both:

```python
# Dict format (most common — project/timeline/color/delivery tools):
{"error": "No project currently open"}
{"error": "Not on Color page. Current page is: edit"}

# String format (media pool, fusion, some delivery tools):
"Error: Clip 'MyClip.mp4' not found in Media Pool"
"Error: Timeline item 'ID-1' not found."
```

A return value that is a non-empty string **beginning with `"Error:"` or
containing `"Failed"` is always a failure**, regardless of HTTP status.

A dict return with key `"error"` is always a failure.

A dict return with key `"warning"` (e.g. render queue already empty) is a
soft failure — the requested state already holds.

A dict return with key `"success": True` or a string **not** beginning with
`"Error"` is a success.

---

## Resources vs Tools

**Resources** (`resolve://…`) are read-only snapshots — use them to read
current state cheaply without side effects.  They are more reliable than
tools for inspection because they never trigger page switches.

**Tools** write or execute operations and may have side effects (page
switches, render jobs started, media imported, etc.).

### Recommended read resources

| Resource URI | What it returns |
|---|---|
| `resolve://version` | Server + Resolve version, connection health |
| `resolve://current-page` | Active page name string |
| `resolve://current-project` | Project name + open status |
| `resolve://current-timeline` | Timeline name, FPS, resolution, timecode |
| `resolve://timelines` | All timeline names in the project |
| `resolve://media-pool-clips` | Flat list of media pool clips with properties |
| `resolve://media-pool-bins` | Bin/folder hierarchy |
| `resolve://timeline-items` | All timeline items (video tracks) with IDs |
| `resolve://timeline-items-list` | Simplified timeline item list |
| `resolve://color/current-node` | Currently selected colour node info |
| `resolve://color/presets` | Saved colour presets |
| `resolve://delivery/render-queue/status` | Render job list + status |
| `resolve://delivery/render-presets` | Available render presets |
| `resolve://project-settings` | All project settings dict |
| `resolve://project/info` | Project name, FPS, resolution |
| `resolve://inspect/resolve` | All callable methods on the Resolve object |
| `resolve://inspect/current-timeline` | All timeline methods (useful for debugging) |

---

## Tool reference by domain

### System & navigation

| Tool | Signature | Notes |
|---|---|---|
| `switch_page` | `(page: str)` | Valid values: `"media"`, `"cut"`, `"edit"`, `"color"`, `"fusion"`, `"fairlight"`, `"deliver"`. |
| `debug_environment` | `()` | Returns env vars, Python paths, Resolve connection status. Use when the server seems broken. |
| `quit_app` | `(force=False, save_project=True)` | Quits Resolve. `force=True` skips confirmation dialogs. |
| `restart_app` | `(wait_seconds=5)` | Restarts Resolve. |
| `open_settings` | `()` | Opens Resolve Project Settings dialog. |
| `open_app_preferences` | `()` | Opens Resolve Preferences dialog. |

---

### Project management

All tools below require **no open project** to be fine except where noted.

| Tool | Signature | Notes |
|---|---|---|
| `open_project` | `(name: str)` | Opens project by exact name. Fails if project does not exist. |
| `create_project` | `(name: str)` | Creates and opens a new project. Fails if name already exists. |
| `save_project` | `()` | Saves the currently open project. Call this after bulk edits. |
| `close_project` | `()` | Closes the current project (does NOT save — call `save_project` first). |
| `set_project_setting` | `(setting_name: str, setting_value: Any)` | Set one setting. Setting names match Resolve API keys (e.g. `"timelineFrameRate"`, `"videoMonitorUse10BitPrecision"`). |
| `set_project_property_tool` | `(property_name: str, property_value: Any)` | Set project-level property (separate from settings). |

Project-related **resources** (read-only): `resolve://projects` (list all project names),
`resolve://current-project`, `resolve://project-settings` (all settings dict),
`resolve://project-setting/{setting_name}` (single setting by key).

**Pattern — open a project and verify:**
```
resolve://projects                     # read resource to list names
open_project(name="My Documentary")   # open it
resolve://current-project              # verify it's active
```

---

### Timeline management

Require an **open project**.

| Tool | Signature | Notes |
|---|---|---|
| `list_timelines_tool` | `()` | Returns list of timeline name strings. |
| `set_current_timeline` | `(name: str)` | Switch active timeline by name. |
| `create_timeline` | `(name: str)` | Creates a timeline with project default settings. |
| `create_empty_timeline` | `(name: str, width=None, height=None, frame_rate=None, ...)` | Creates with custom settings. |
| `delete_timeline` | `(name: str)` | Deletes timeline. Refuses to delete the only/current timeline — switch first. |
| `set_current_frame` | `(frame: int)` | Move the playhead to a frame number (0-based from timeline start). |
| `add_marker` | `(frame: int = None, color: str = "Blue", note: str = "")` | Add a timeline marker. `frame=None` uses current playhead. Valid colors: `"Blue"`, `"Cyan"`, `"Green"`, `"Yellow"`, `"Red"`, `"Pink"`, `"Purple"`, `"Fuchsia"`, `"Rose"`, `"Lavender"`, `"Sky"`, `"Mint"`, `"Lemon"`, `"Sand"`, `"Cocoa"`, `"Cream"`. |
| `razor_timeline` | `(frame: int = None)` | Cut all clips at `frame` (or current playhead if None). |

Timeline-related **resources** (read-only): `resolve://timelines` (list all timeline names),
`resolve://current-timeline` (name, FPS, resolution, timecode),
`resolve://timeline-tracks/{timeline_name}` (track structure).

---

### Timeline items (clips in the timeline)

Require an **active timeline**.  Most tools take a `timeline_item_id` which
comes from `get_timeline_items()` or the resource `resolve://timeline-items`.

**Critical workflow — always get IDs first:**
```
resolve://timeline-items            # read resource to get all item IDs
# → [{id: "abc123", name: "Shot01.mov", track: "V1", start: 0, end: 240}, ...]
set_timeline_item_name(timeline_item_id="abc123", name="IntroShot")
```

| Tool | Signature | Key params |
|---|---|---|
| `get_timeline_items` | `()` | Returns all video track items with IDs, names, start/end frames. |
| `set_timeline_item_name` | `(timeline_item_id, name)` | Rename a timeline item. |
| `set_timeline_item_transform` | `(timeline_item_id, zoom_x=None, zoom_y=None, pan=None, tilt=None, rotation=None, ...)` | Transform properties. |
| `set_timeline_item_crop` | `(timeline_item_id, left=None, right=None, top=None, bottom=None)` | Crop by pixel values. |
| `set_timeline_item_composite` | `(timeline_item_id, mode=None, opacity=None)` | Composite mode + opacity (0.0–1.0). |
| `set_timeline_item_retime` | `(timeline_item_id, speed=None, ...)` | Retime/speed. `speed=200.0` = 2× speed. |
| `set_timeline_item_stabilization` | `(timeline_item_id, enabled=None, ...)` | Stabilization settings. |
| `set_timeline_item_audio` | `(timeline_item_id, volume=None, pan=None, ...)` | Audio properties. |

---

### Media pool

Require an **open project**.  Most tools search by clip **name** — names
must be exact.

| Tool | Signature | Notes |
|---|---|---|
| `list_media_pool_items` | `()` | Verbose flat listing including all subfolders. |
| `import_media` | `(file_path: str)` | Absolute path to file on disk. Fails if path does not exist. |
| `delete_media` | `(clip_name: str)` | Delete from media pool by exact name. |
| `create_bin` | `(name: str)` | Create a sub-bin in the root folder. |
| `move_media_to_bin` | `(clip_name: str, bin_name: str)` | Move clip to bin. Use `"master"` for root. |
| `add_clip_to_timeline` | `(clip_name: str, timeline_name: str = None)` | Appends clip to current (or named) timeline. |
| `create_timeline_from_clips` | `(timeline_name: str, clip_names: List[str])` | Creates a new timeline and populates it in clip order. |
| `auto_sync_audio` | `(clip_names: List[str], sync_method="waveform", append_mode=False, target_bin=None)` | Sync audio. `sync_method`: `"waveform"` or `"timecode"`. Requires ≥2 clips. |
| `unlink_clips` | `(clip_names: List[str])` | Disconnect clips from their media files (offline). |
| `relink_clips` | `(clip_names: List[str], media_paths=None, folder_path=None, recursive=False)` | Relink offline clips. Provide EITHER `media_paths` (one per clip) OR `folder_path`. |
| `create_sub_clip` | `(clip_name, start_frame, end_frame, sub_clip_name=None, bin_name=None)` | Subclip from in/out frames. Returns an error on Resolve builds that lack `CreateSubClip` — see limitations table. |
| `link_proxy_media` | `(clip_name: str, proxy_file_path: str)` | Link a proxy media file to a clip. |
| `unlink_proxy_media` | `(clip_name: str)` | Remove proxy link. |
| `replace_clip` | `(clip_name: str, replacement_path: str)` | Replace source media for a clip. |
| `transcribe_audio` | `(clip_name: str, language="en-US")` | AI transcription of a single clip. |
| `transcribe_folder_audio` | `(folder_name: str, language="en-US")` | Transcribe all clips in a bin. |
| `clear_transcription` | `(clip_name: str)` | Clear AI transcription from a single clip. |
| `clear_folder_transcription` | `(folder_name: str)` | Clear transcriptions from all clips in a bin. |
| `export_folder` | `(folder_name: str, export_path: str, export_type="DRB")` | Export a bin. Types: `"DRB"`, `"CSV"`, `"TSV"`. |

Media pool **resources** (read-only): `resolve://media-pool-clips` (all clips in root bin),
`resolve://media-pool-bins` (bin hierarchy with clip counts),
`resolve://media-pool-bin/{bin_name}` (clips in a specific bin).

---

### Colour (Color page required)

**Always call `switch_page(page="color")` before these tools.**
Colour tools also require a **clip to be selected** in the Color page timeline.
Navigate with `set_current_timeline` then `set_current_frame` to position the
playhead on the intended clip.

| Tool | Signature | Notes |
|---|---|---|
| `add_node` | `(node_type="serial", label=None)` | Add a node. `node_type`: `"serial"`, `"parallel"`, `"layer"`. |
| `apply_lut` | `(lut_path: str, node_index: int = None)` | Apply a LUT file (.cube, .3dl, .mga) to a node. `node_index=None` uses the currently selected node. Path must exist on disk. |
| `set_color_wheel_param` | `(wheel: str, param: str, value: float, node_index: int = None)` | Adjust a colour wheel parameter. `wheel`: `"lift"`, `"gamma"`, `"gain"`, `"offset"`. `param`: `"red"`, `"green"`, `"blue"`, `"master"` (Y/luma channel). `value` range: typically −1.0 to +1.0. |
| `copy_grade` | `(source_clip_name=None, target_clip_name=None, mode="full")` | Copy grade between clips. `mode`: `"full"` (entire grade), `"current_node"` (selected node only), `"all_nodes"` (node graph). |
| `apply_color_preset` | `(preset_id=None, preset_name=None, clip_name=None)` | Apply a saved preset by ID or name. |
| `save_color_preset` | `(clip_name=None, preset_name=None, album_name="DaVinci Resolve")` | Save current grade as a preset. |
| `delete_color_preset` | `(preset_id=None, preset_name=None, album_name=None)` | Delete a preset. |
| `create_color_preset_album` | `(album_name: str)` | Create a preset album. |
| `delete_color_preset_album` | `(album_name: str)` | Delete a preset album. |
| `export_lut` | `(clip_name=None, lut_path=None, format=None)` | Export grade as a LUT file. |
| `export_all_powergrade_luts` | `(export_dir: str)` | Export all PowerGrade LUTs to a directory. |

Colour **resources** (read-only): `resolve://color/current-node` (selected node info),
`resolve://color/presets` (saved colour presets).

**Example — push a colour correction to a specific clip:**
```
switch_page(page="color")
set_current_timeline(name="Main Edit")
set_current_frame(frame=240)          # position on the target clip
add_node(node_type="serial", label="Grade")
set_color_wheel_param(wheel="lift", param="master", value=-0.05)
set_color_wheel_param(wheel="gain", param="master", value=0.1)
apply_lut(lut_path="/Library/LUTs/Kodak5219.cube")
save_project()
```

---

### Keyframes

Keyframe tools take `timeline_item_id` from `get_timeline_items()`.

| Tool | Signature | Notes |
|---|---|---|
| `enable_keyframes` | `(timeline_item_id, keyframe_mode="All")` | Enable keyframing. Must call before adding keyframes. `mode`: `"All"`, `"Color"`, `"Sizing"`. |
| `add_keyframe` | `(timeline_item_id, property_name, frame, value)` | Add a keyframe. |
| `modify_keyframe` | `(timeline_item_id, property_name, frame, new_value=None, new_frame=None)` | Move or change a keyframe. |
| `delete_keyframe` | `(timeline_item_id, property_name, frame)` | Delete a keyframe at frame. |
| `set_keyframe_interpolation` | `(timeline_item_id, property_name, frame, interpolation_type)` | `interpolation_type`: `"Linear"`, `"Bezier"`, `"Ease"`. |

---

### Delivery / Render

**Always call `switch_page(page="deliver")` before these tools.**

| Tool | Signature | Notes |
|---|---|---|
| `add_to_render_queue` | `(preset_name, timeline_name=None, use_in_out_range=False)` | Add a render job. `preset_name` must match a preset from `resolve://delivery/render-presets`. Omit `timeline_name` to use current timeline. |
| `add_to_render_queue_json` | `(settings_json: str)` | Add a job with full custom settings as JSON string. Advanced use. |
| `start_render` | `()` | Start rendering all queued jobs. Returns `{"success": True, "jobs_count": N}`. |
| `clear_render_queue` | `()` | Remove all jobs. Stops rendering first if in progress. |

Delivery **resources** (read-only): `resolve://delivery/render-queue/status` (queued jobs
with status/progress), `resolve://delivery/render-presets` (available render presets).

**Example — render the current timeline to YouTube 1080p:**
```
switch_page(page="deliver")
resolve://delivery/render-presets      # confirm "YouTube 1080p" exists
add_to_render_queue(preset_name="YouTube 1080p")
start_render()
```

---

### Fusion effects

`add_fusion_effect` and `add_fusion_generator` take a `timeline_item_id`
(from `get_timeline_items()`), not a clip name.

| Tool | Signature | Notes |
|---|---|---|
| `add_fusion_effect` | `(timeline_item_id, effect_name, settings=None)` | Add a Fusion tool node (e.g. `"Vignette"`, `"Blur"`, `"ColorCorrector"`). `settings` is a dict of input-name → value. Automatically wires the tool into the MediaIn→MediaOut pipeline. |
| `add_fusion_generator` | `(timeline_item_id, generator_name, settings=None)` | Add a generator (e.g. `"TextPlus"`, `"Background"`). Adds a Merge node and wires Background=MediaIn, Foreground=Generator, MediaOut=Merge output. |

---

### Cache & proxy

| Tool | Signature | Notes |
|---|---|---|
| `set_cache_mode` | `(mode: str)` | `"none"`, `"local"`, `"network"`. |
| `set_optimized_media_mode` | `(mode: str)` | `"none"`, `"proxy_only"`, `"original_plus_proxy"`, `"smart"`. |
| `set_proxy_mode` | `(mode: str)` | `"none"`, `"half"`, `"quarter"`. |
| `set_proxy_quality` | `(quality: str)` | `"source"`, `"1/2"`, `"1/4"`, `"1/8"`. |
| `set_cache_path` | `(path_type: str, path: str)` | `path_type`: `"local"` or `"network"`. |
| `generate_optimized_media` | `(clip_names: List[str] = None)` | `clip_names=None` generates for all clips. |
| `delete_optimized_media` | `(clip_names: List[str] = None)` | `clip_names=None` deletes all. |

---

### Project properties, format & colour science

| Tool | Signature | Notes |
|---|---|---|
| `set_timeline_format_tool` | `(width, height, frame_rate, interlaced=False)` | Set master timeline resolution and FPS. |
| `set_color_science_mode_tool` | `(mode: str)` | `"davinci_yrgb"`, `"davinci_yrgb_color_managed"`, `"aces_cc"`, `"aces_cct"`. |
| `set_color_space_tool` | `(color_space: str, gamma: str = None)` | e.g. `set_color_space_tool("DaVinci Wide Gamut", "DaVinci Intermediate")`. |
| `set_superscale_settings_tool` | `(enabled: bool, quality: int = 0)` | SuperScale: `quality` 0=auto, 1=enhanced, 2=ultra. |

---

### Layout presets

| Tool | Signature | Notes |
|---|---|---|
| `save_layout_preset_tool` | `(preset_name)` | Save current UI layout. |
| `load_layout_preset_tool` | `(preset_name)` | Restore a layout. |
| `export_layout_preset_tool` | `(preset_name, export_path)` | Save to file. |
| `import_layout_preset_tool` | `(import_path, preset_name=None)` | Load from file. |
| `delete_layout_preset_tool` | `(preset_name)` | Delete a layout. |

---

### Inspection (debugging)

Use these when a tool behaves unexpectedly or you need to discover what
methods are available on an object.

| Tool / Resource | Notes |
|---|---|
| `object_help(object_type)` | Human-readable list of methods for `"resolve"`, `"project"`, `"timeline"`, `"media_pool"`, `"clip"`, etc. |
| `inspect_custom_object(object_path)` | Inspect arbitrary dotted path, e.g. `"resolve.GetProjectManager().GetCurrentProject()"`. |
| `resolve://inspect/resolve` | All methods on the top-level Resolve object. |
| `resolve://inspect/current-project` | All methods on the current project. |
| `resolve://inspect/current-timeline` | All methods on the current timeline. |
| `resolve://inspect/media-pool` | All methods on the media pool. |
| `debug_environment` | Server environment, paths, scripting connection. |

---

### Scripting (advanced, requires opt-in)

The `execute_python` tool is **disabled by default**.  It runs arbitrary
Python code against the live Resolve scripting API.  Enable it only when you
understand the security implications:

```bash
export RESOLVE_MCP_ALLOW_EXEC=1   # before starting the server
```

When enabled, the code runs in an isolated namespace with:
`resolve`, `project_manager`, `project`, `media_pool`, `timeline`
pre-bound.  Do not use `execute_python` unless the dedicated tools cannot
accomplish the task — prefer the typed tools.

---

## Common workflows

### Workflow 1 — Inspect a project before making changes
```
1. resolve://version                      # confirm connected
2. resolve://current-project             # confirm project is open
3. resolve://timelines                   # list all timelines
4. set_current_timeline(name="...")      # activate the right one
5. resolve://current-timeline           # confirm FPS, resolution, timecode
6. resolve://timeline-items             # get all clip IDs and positions
```

### Workflow 2 — Import media and build a rough cut
```
1. open_project(name="My Project")
2. import_media(file_path="/path/to/clip1.mp4")
3. import_media(file_path="/path/to/clip2.mp4")
4. create_bin(name="Selects")
5. move_media_to_bin(clip_name="clip1.mp4", bin_name="Selects")
6. create_timeline_from_clips(
       timeline_name="Rough Cut",
       clip_names=["clip1.mp4", "clip2.mp4"]
   )
7. save_project()
```

### Workflow 3 — Colour grade a specific clip
```
1. switch_page(page="color")
2. set_current_timeline(name="Main Edit")
3. resolve://timeline-items              # find which frame the target clip is at
4. set_current_frame(frame=120)          # position on the clip
5. add_node(node_type="serial", label="Primary")
6. set_color_wheel_param(wheel="gain", param="master", value=0.08)
7. apply_lut(lut_path="/path/to/grade.cube")
8. save_project()
```

### Workflow 4 — Render the timeline
```
1. switch_page(page="deliver")
2. resolve://delivery/render-presets     # list available presets
3. add_to_render_queue(preset_name="H.264 Master")
4. resolve://delivery/render-queue/status  # confirm job is queued
5. start_render()
6. # Poll resolve://delivery/render-queue/status to monitor progress
```

### Workflow 5 — Add a Fusion effect to a timeline clip
```
1. switch_page(page="edit")
2. resolve://timeline-items              # get clip IDs
# → [{id: "abc123", name: "Shot01.mov", ...}]
3. add_fusion_effect(
       timeline_item_id="abc123",
       effect_name="Vignette",
       settings={"Gain": 0.7, "Softness": 0.5}
   )
```

---

## Known limitations & gotchas

| Situation | What happens | Workaround |
|---|---|---|
| Resolve is not running | All tools return connection errors | Start Resolve first; use `debug_environment` to diagnose |
| No project open | Most tools return `"No project currently open"` | Call `open_project` or `create_project` first |
| Wrong page | Colour/delivery tools return page error | Call `switch_page` first |
| Colour tools with no clip selected | Returns `"No clip is currently selected"` | Use `set_current_frame` to land on a clip |
| `add_to_render_queue` with unknown preset | Returns preset-not-found error | Read `resolve://delivery/render-presets` first to get exact names |
| `import_media` with relative path | Fails silently or with OS error | Always use absolute paths |
| `delete_timeline` on the only timeline | Explicitly refused | Create another timeline first |
| Clip name contains special characters | Name-based search is exact-match only | Read `resolve://media-pool-clips` to discover exact names first |
| `create_sub_clip` with unsupported Resolve build | Returns "not supported" error | No automatic fallback — tell the user their Resolve build lacks `CreateSubClip` and they must create the subclip manually in the Media Pool |
| Keyframe tools | Must call `enable_keyframes` first | Always enable before adding keyframes |
| Cloud project tools | Require a Blackmagic Cloud subscription | Tools return errors gracefully if not configured |
| Linux | Resolve scripting API on Linux is experimental | Server works; some Resolve features may be absent |

---

## Memory MCP

A memory MCP server with timestamps is configured in this Claude Code
installation (local sessions only — remote/web containers cannot reach it).

**Store these facts to avoid rediscovering them after context resets:**

- Active project name and database location
- Timeline names, FPS, and resolution
- Clip names and timeline item IDs (expensive to re-query)
- Render preset names confirmed working

Useful things to store: active project name, which timelines exist, clip
names / IDs discovered this session, render job IDs.

---

## Quick diagnostics checklist

If tools are failing unexpectedly, run through this list:

```
1. debug_environment()           → check RESOLVE_SCRIPT_API, Python paths
2. resolve://version             → is Resolve connected?
3. resolve://current-project     → is a project open?
4. resolve://current-page        → are you on the right page?
5. resolve://current-timeline    → is a timeline active?
6. resolve://inspect/resolve     → does the scripting API expose expected methods?
```
