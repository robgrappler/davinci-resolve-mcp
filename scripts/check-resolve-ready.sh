#!/usr/bin/env bash
# Pre-launch checks for DaVinci Resolve MCP.
#
# Verifies:
#   1. DaVinci Resolve process is running.
#   2. RESOLVE_SCRIPT_API / RESOLVE_SCRIPT_LIB env vars point at real paths.
#   3. The davinci_resolve_mcp package imports successfully (i.e. it has
#      been installed via `pip install -e .` or similar).
#
# This script does NOT start the server — that's the MCP client's job, via
# the configured `python -m davinci_resolve_mcp` or `davinci-resolve-mcp`
# console script.

set -u

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

status=0

print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

ok() { echo -e "${GREEN}✓ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠ $1${NC}"; }
fail() { echo -e "${RED}✗ $1${NC}"; status=1; }

print_section "DaVinci Resolve MCP Pre-Launch Check"

# 1. DaVinci Resolve process
if pgrep -x Resolve >/dev/null 2>&1 || pgrep -f "[D]aVinci Resolve" >/dev/null 2>&1; then
    ok "DaVinci Resolve is running"
else
    fail "DaVinci Resolve is not running — start it before launching the MCP server"
fi

# 2. Environment variables
case "$(uname -s)" in
    Darwin)
        default_api="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
        default_lib="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
        ;;
    Linux)
        default_api="/opt/resolve/Developer/Scripting"
        default_lib="/opt/resolve/libs/Fusion/fusionscript.so"
        ;;
    *)
        default_api=""
        default_lib=""
        ;;
esac

api_path="${RESOLVE_SCRIPT_API:-$default_api}"
lib_path="${RESOLVE_SCRIPT_LIB:-$default_lib}"

if [ -n "$api_path" ] && [ -d "$api_path" ]; then
    ok "RESOLVE_SCRIPT_API = $api_path"
else
    fail "RESOLVE_SCRIPT_API not set or path missing: '$api_path'"
fi

if [ -n "$lib_path" ] && [ -f "$lib_path" ]; then
    ok "RESOLVE_SCRIPT_LIB = $lib_path"
else
    fail "RESOLVE_SCRIPT_LIB not set or file missing: '$lib_path'"
fi

# 3. Package importable — prefer the project venv created by install.sh,
# fall back to whatever Python is on PATH.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"

if [ -x "$VENV_PYTHON" ]; then
    py="$VENV_PYTHON"
elif command -v python3 >/dev/null 2>&1; then
    py="python3"
elif command -v python >/dev/null 2>&1; then
    py="python"
else
    py=""
fi

if [ -z "$py" ]; then
    fail "No Python interpreter found"
elif "$py" -c "import davinci_resolve_mcp" >/dev/null 2>&1; then
    ok "davinci_resolve_mcp package importable ($py)"
else
    fail "davinci_resolve_mcp not installed in $py. Run: scripts/setup/install.sh"
fi

echo ""
if [ $status -eq 0 ]; then
    ok "All checks passed. Configure your MCP client to launch: $py -m davinci_resolve_mcp"
else
    warn "One or more checks failed. See messages above."
fi

exit $status
