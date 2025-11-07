#!/bin/bash
# Wrapper script to run the DaVinci Resolve MCP Server with the virtual environment

# Source environment variables if not already set
if [ -z "$RESOLVE_SCRIPT_API" ]; then
  source "/Users/ppt04/.zshrc"
fi

# Activate virtual environment and run server
"/Users/ppt04/Github/davinci-resolve-mcp/scripts/venv/bin/python" "/Users/ppt04/Github/davinci-resolve-mcp/scripts/../src/main.py" "$@"
