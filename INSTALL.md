# DaVinci Resolve MCP — Installation Guide

This guide walks through installing the DaVinci Resolve MCP server and
configuring it for an AI assistant (Cursor, Claude Desktop, etc.).

## Prerequisites

- DaVinci Resolve 18.5+ (Free or Studio) installed
- Python 3.10+ on PATH
- The AI assistant you plan to use (Cursor, Claude Desktop, …)

## 1. Install the package

```bash
git clone https://github.com/samuelgursky/davinci-resolve-mcp.git
cd davinci-resolve-mcp
./scripts/setup/install.sh         # macOS / Linux
# or:  scripts\setup\install.bat   (Windows)
```

The installer creates a virtualenv at `./venv/`, runs `pip install -e .`,
and prints the launch command (`python -m davinci_resolve_mcp`) for use in
your MCP client's configuration.

### Manual install

If you prefer to set things up yourself:

```bash
python3 -m venv venv
source venv/bin/activate           # Windows:  venv\Scripts\activate
pip install -e .
```

## 2. Configure the scripting environment

DaVinci Resolve's Python scripting API needs two environment variables.
The MCP client config templates in `config/` already include them, but if
you'd rather set them globally:

**macOS / Linux**
```bash
export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
export PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
```

**Windows (PowerShell)**
```powershell
$env:RESOLVE_SCRIPT_API = "C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
$env:RESOLVE_SCRIPT_LIB = "C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
$env:PYTHONPATH = "$env:PYTHONPATH;$env:RESOLVE_SCRIPT_API\Modules\"
```

Add these to your shell profile (`~/.zshrc`, `~/.bashrc`, your PowerShell
profile, …) to persist them.

## 3. Configure your MCP client

Copy a template from `config/` and adjust the paths:

| Client          | Platform | Template                                                  |
|-----------------|----------|-----------------------------------------------------------|
| Cursor          | macOS    | `config/macos/cursor-mcp-config.template.json`            |
| Cursor          | Windows  | `config/windows/cursor-mcp-config.template.json`          |
| Claude Desktop  | macOS    | `config/macos/claude-desktop-config.template.json`        |
| Claude Desktop  | Windows  | `config/windows/claude-desktop-config.template.json`      |

Replace `${PROJECT_ROOT}` with the absolute path to your checkout. The
templates launch the server via `python -m davinci_resolve_mcp`.

Drop the resulting file into the client's MCP config location:

- **Cursor:** `~/.cursor/mcp.json` (or `%USERPROFILE%\.cursor\mcp.json`)
- **Claude Desktop:** `~/Library/Application Support/Claude/claude_desktop_config.json`
  (or `%APPDATA%\Claude\claude_desktop_config.json`)

## 4. Verify the setup

With DaVinci Resolve running:

```bash
./scripts/check-resolve-ready.sh        # macOS / Linux
# or:  scripts\check-resolve-ready.bat  (Windows)
```

The preflight checks:
1. DaVinci Resolve process is running.
2. `RESOLVE_SCRIPT_API` / `RESOLVE_SCRIPT_LIB` resolve to real paths.
3. `davinci_resolve_mcp` package imports successfully.

Then start your MCP client and ask it to "list timelines" or "what version
of DaVinci Resolve is running?" to confirm end-to-end.

## Optional: enabling `execute_python`

The `execute_python` tool runs arbitrary Python with full access to the
Resolve scripting API and is **disabled by default**. To enable, set
`RESOLVE_MCP_ALLOW_EXEC=1` in the MCP client's environment (`env` block in
the JSON config). Only enable this if you understand that any connected
MCP client can then execute arbitrary code.

## Troubleshooting

- **"Failed to get Resolve object"** — DaVinci Resolve is not running, or
  the scripting paths are wrong. Re-run the preflight script.
- **"davinci_resolve_mcp not installed"** — re-run the installer, or
  `pip install -e .` from the project root in the same Python environment
  the MCP client is using.
- **MCP client reports "client closed"** — verify the absolute paths in
  the client config; relative paths break inside MCP client launchers.
- **Env vars don't stick** — add them to your shell profile, or put them
  in the `env` block of the MCP client config so they're set for the
  child process.

If problems persist, file an issue on the GitHub repository.
