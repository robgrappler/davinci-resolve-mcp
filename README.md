# DaVinci Resolve MCP Server

[![Version](https://img.shields.io/badge/version-1.3.8-blue.svg)](https://github.com/samuelgursky/davinci-resolve-mcp/releases)
[![DaVinci Resolve](https://img.shields.io/badge/DaVinci%20Resolve-18.5+-darkred.svg)](https://www.blackmagicdesign.com/products/davinciresolve)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/downloads/)
[![macOS](https://img.shields.io/badge/macOS-stable-brightgreen.svg)](https://www.apple.com/macos/)
[![Windows](https://img.shields.io/badge/Windows-stable-brightgreen.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server that connects AI coding assistants
(Cursor, Claude Desktop, etc.) to DaVinci Resolve, letting them query and
control DaVinci Resolve through natural language.

For a comprehensive list of implemented and planned tools, see
[docs/FEATURES.md](docs/FEATURES.md).

## Requirements

- **macOS** or **Windows** with DaVinci Resolve 18.5+ installed and running
- **Python 3.10+** (required by the MCP SDK)

## Security

The optional `execute_python` tool lets an MCP client run arbitrary Python
code on your machine with full access to the DaVinci Resolve scripting API.
Because MCP tools are invoked by AI assistants that may process untrusted
content (clip names, markers, transcripts), this tool is **disabled by
default**.

To enable it, set the environment variable before starting the server:

```bash
export RESOLVE_MCP_ALLOW_EXEC=1
```

Only enable this if you understand that any connected MCP client can then
execute arbitrary code.

## Quick Start

```bash
git clone https://github.com/samuelgursky/davinci-resolve-mcp.git
cd davinci-resolve-mcp
./scripts/setup/install.sh        # macOS / Linux
# or:  scripts\setup\install.bat  (Windows)
```

The installer creates `./venv/`, runs `pip install -e .`, and prints the
launch command you need to paste into your MCP client's configuration.

### Preflight check

Once installed, verify the environment any time the server seems off:

```bash
./scripts/check-resolve-ready.sh        # macOS / Linux
# or:  scripts\check-resolve-ready.bat  (Windows)
```

It confirms DaVinci Resolve is running, the scripting paths resolve, and
the `davinci_resolve_mcp` package imports successfully. It does **not**
start the server — that's the MCP client's job.

## Launching the server

The server runs as a Python module:

```bash
python -m davinci_resolve_mcp
```

After `pip install -e .` you also have an equivalent console script:

```bash
davinci-resolve-mcp
```

Configure your MCP client to invoke one of these commands. Templates for
Cursor and Claude Desktop live under [`config/`](config/).

### Environment variables

The server needs DaVinci Resolve's scripting paths exposed via env vars:

**macOS**
```bash
export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
export PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
```

**Windows**
```cmd
set RESOLVE_SCRIPT_API=C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting
set RESOLVE_SCRIPT_LIB=C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll
set PYTHONPATH=%PYTHONPATH%;%RESOLVE_SCRIPT_API%\Modules
```

The MCP client config templates in `config/` include these in their `env`
block so you don't need to set them in your shell.

## Configuration

Templates for popular MCP clients live in [`config/`](config/):
- `config/cursor-mcp-example.json` — Cursor (path-only example)
- `config/macos/claude-desktop-config.template.json` — Claude Desktop, macOS
- `config/macos/cursor-mcp-config.template.json` — Cursor, macOS
- `config/windows/claude-desktop-config.template.json` — Claude Desktop, Windows
- `config/windows/cursor-mcp-config.template.json` — Cursor, Windows

Replace `${PROJECT_ROOT}` with the absolute path to your checkout.

## Project structure

```
davinci-resolve-mcp/
├── src/davinci_resolve_mcp/    # The MCP server package
│   ├── __main__.py             # Entry point (python -m davinci_resolve_mcp)
│   ├── server.py               # FastMCP server factory
│   ├── adapters/               # Resolve scripting API adapter
│   ├── api/                    # Resolve operations (color, media, timeline, ...)
│   ├── handlers/               # Tool/resource registration per domain
│   └── utils/                  # Platform helpers, response envelopes, etc.
├── tests/unit/                 # Pytest suite (parity + gate tests)
├── config/                     # MCP client configuration templates
├── scripts/                    # Installer + preflight check
│   ├── check-resolve-ready.{sh,bat}
│   ├── README.md
│   └── setup/install.{sh,bat}
├── docs/                       # Documentation, including AUDIT.md
├── examples/                   # Usage examples for the scripting API
├── pyproject.toml              # Package metadata
└── README.md
```

## Troubleshooting

1. **Server can't connect to Resolve.** Make sure DaVinci Resolve is
   running, then re-run the preflight script.
2. **`davinci_resolve_mcp` not found.** Re-run the installer, or
   `pip install -e .` directly.
3. **Env vars don't stick.** Either export them in your shell profile or
   put them in the MCP client config's `env` block (see templates).

For more, see [INSTALL.md](INSTALL.md) and
[docs/AUDIT.md](docs/AUDIT.md).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT

## Author

Samuel Gursky (samgursky@gmail.com) — [github.com/samuelgursky](https://github.com/samuelgursky)
