#!/bin/bash
# Wrapper script to run the DaVinci Resolve MCP Server with the virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment and run server
if [ -x "$PROJECT_ROOT/venv/bin/python" ]; then
  PYTHON="$PROJECT_ROOT/venv/bin/python"
else
  PYTHON="python3"
fi

exec "$PYTHON" "$PROJECT_ROOT/src/main.py" "$@"
