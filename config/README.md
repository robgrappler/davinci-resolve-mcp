# DaVinci Resolve MCP Configuration Templates

Templates for wiring popular MCP clients to the DaVinci Resolve MCP
server. The server is launched as the Python module
`python -m davinci_resolve_mcp` (or the equivalent `davinci-resolve-mcp`
console script installed by the package).

## ⚠️ Replace the placeholders

Every template contains `${PROJECT_ROOT}` placeholders that you must
replace with the absolute path to your checkout. MCP clients do not
expand these variables automatically.

- macOS: `${PROJECT_ROOT}` → e.g. `/Users/username/davinci-resolve-mcp`
- Windows: `${PROJECT_ROOT}` → e.g. `C:\Users\username\davinci-resolve-mcp`

Failure to replace the placeholders is the most common cause of "client
closed" errors.

## Available templates

| Client          | Platform | File                                              |
|-----------------|----------|---------------------------------------------------|
| Cursor          | macOS    | `macos/cursor-mcp-config.template.json`           |
| Cursor          | Windows  | `windows/cursor-mcp-config.template.json`         |
| Claude Desktop  | macOS    | `macos/claude-desktop-config.template.json`       |
| Claude Desktop  | Windows  | `windows/claude-desktop-config.template.json`     |
| Cursor (example, generic) | —      | `cursor-mcp-example.json`              |

## Where to drop the file

- **Cursor:** `~/.cursor/mcp.json` (macOS) or
  `%USERPROFILE%\.cursor\mcp.json` (Windows)
- **Claude Desktop:**
  `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
  or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

## Example (macOS, after substitution)

```json
{
  "mcpServers": {
    "davinci-resolve": {
      "name": "DaVinci Resolve MCP",
      "command": "/Users/username/davinci-resolve-mcp/venv/bin/python",
      "args": ["-m", "davinci_resolve_mcp"]
    }
  }
}
```

The macOS / Windows templates also include an `env` block that pre-sets
`RESOLVE_SCRIPT_API`, `RESOLVE_SCRIPT_LIB`, and `PYTHONPATH` for the
launched server process.

## Enabling `execute_python`

Add `RESOLVE_MCP_ALLOW_EXEC: "1"` to the `env` block to opt in to the
`execute_python` tool. This lets any connected client run arbitrary
Python on your machine — only enable if you understand the risk.
