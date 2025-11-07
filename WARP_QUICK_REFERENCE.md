# DaVinci Resolve MCP - Warp Quick Reference

## ⚡ Quick Start

**IMPORTANT:** DaVinci Resolve **must be running** before using these commands!

After installing and restarting Warp, you can control DaVinci Resolve through natural language commands.

## ✅ Verified Working Commands (macOS)

These commands have been tested and verified to work on macOS:

### 🎬 Core Operations
- "What version of DaVinci Resolve is running?"
- "Get the product name" (checks if Studio or Free version)
- "What page am I currently on?"
- "Switch to the Edit page"
- "Switch to the Color page"
- "Switch to the Deliver page"

### 📁 Project Management
- "List all projects"
- "What's the current project name?"
- "Open project named [project_name]"
- "Create a new project called [project_name]"
- "Save the current project"
- "Close the current project"

### 🎞️ Timeline Operations
- "List all timelines in the current project"
- "Get current timeline info"
- "Create a new timeline called [timeline_name]"
- "Switch to timeline [timeline_name]"

### 📂 Media Pool Operations
- "Import media from [file_path]"
- "List media in the media pool"
- "Create a media bin called [bin_name]"
- "Add [clip_name] to the timeline"
- "Get properties of [clip_name]"

### 🎨 Color Page Operations
- "Apply a LUT to the current clip"
- "Get color grade information"
- "Create a color version"
- "Apply color correction to current clip"

### 🎬 Delivery Operations
- "Clear the render queue"
- "List render presets"
- "Check render status"

## ⚠️ Commands That Need Testing

These are implemented but haven't been fully verified yet:

### Timeline Features
- "Add a marker at frame [number]"
- "Delete marker at frame [number]"
- "Get all markers in timeline"
- "Add video/audio tracks"
- "Get timeline items"

### Media Pool Features
- "Set clip metadata"
- "Add clip markers"
- "Organize media into bins"
- "Relink offline media"
- "Sync audio between clips"

### Color Grading (Advanced)
- "Add a color node"
- "Set primary color wheels"
- "Export color grade as DRX"
- "Create color group"
- "Apply gallery still"

### Rendering
- "Add render job for [timeline_name]"
- "Start rendering"
- "Get render job status"

## 🐞 Known Issues

### Color Page
- Adding nodes may fail if no clips are selected
- Color wheel adjustments need existing grade objects

### Delivery Page  
- Adding render jobs sometimes fails (use clear queue instead)

### Media Pool
- Creating items with duplicate names will fail
- Better to check for existing items first

## 💡 Tips for Best Results

1. **Be specific with names:** Use exact project, timeline, and clip names
2. **Check current state first:** Ask "what's the current project?" before making changes
3. **One step at a time:** Break complex workflows into individual commands
4. **Start simple:** Test basic commands before trying advanced operations
5. **DaVinci must be running:** Always have DaVinci Resolve open with a project loaded

## 🔧 Troubleshooting

### Connection Issues
```
Error: Cannot connect to DaVinci Resolve
```
**Solution:** Make sure DaVinci Resolve is running before using commands

### Environment Variables
If you see import errors, the environment variables may not be set correctly. They should be:
```bash
RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
PYTHONPATH="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
```

These are automatically set in the Warp MCP configuration.

### MCP Server Not Found
If Warp doesn't recognize DaVinci Resolve commands:
1. Restart Warp to reload MCP configuration
2. Check `~/.config/warp/mcp_config.json` for the davinci-resolve entry
3. Verify the Python path: `/Users/ppt04/Github/davinci-resolve-mcp/venv/bin/python`

## 📖 Example Workflows

### Basic Edit Workflow
```
1. "List all projects"
2. "Open project named MyProject"
3. "List all timelines"
4. "Switch to timeline Main_Edit"
5. "Switch to Edit page"
6. "Import media from /path/to/video.mp4"
7. "Add video.mp4 to timeline"
```

### Color Grading Workflow
```
1. "Open project named MyProject"
2. "Switch to timeline Main_Edit"
3. "Switch to Color page"
4. "Get current clip info"
5. "Apply color correction"
6. "Create color version named v1"
7. "Save project"
```

### Export Workflow
```
1. "Open project named MyProject"
2. "Switch to timeline Main_Edit"
3. "Switch to Deliver page"
4. "Clear render queue"
5. "List render presets"
6. "Save project"
```

## 🚀 Advanced Features

### Object Inspection
The MCP server supports introspection of DaVinci Resolve API objects:
- "List available methods for current timeline"
- "Get properties of current project"
- "Inspect API version"

### Batch Operations
You can process multiple items:
- "Import all media files from folder /path/to/media/"
- "Apply color grade to all clips in timeline"

### Automation Scripts
For complex workflows, check out:
- `scripts/batch_automation.py` - Pre-built automation workflows
- `scripts/benchmark_server.py` - Performance testing

## 📚 Additional Resources

- **Full Feature List:** `docs/FEATURES.md`
- **Installation Guide:** `INSTALL.md`
- **Project README:** `README.md`
- **Tools Documentation:** `docs/TOOLS_README.md`

## 🎯 Success Rates

Based on testing (macOS):
- ✅ Core Features: ~44% verified working
- ✅ Project Management: ~11% verified working
- ✅ Timeline Operations: ~17% verified working
- ⚠️ Media Pool: Testing needed
- ⚠️ Color Page: Testing needed (some issues)
- ⚠️ Delivery Page: Partial support

**Total Implementation:** 202 features (100% implemented, 8% fully verified on macOS)

---

**Note:** This MCP server is actively being developed. Features marked as ⚠️ are implemented but may need additional testing or have known limitations. Always test commands in a safe environment before using in production.

**Windows Users:** Most features should work on Windows, but testing is still needed. Environment variable paths will differ.
