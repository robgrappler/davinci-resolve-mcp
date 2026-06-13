#!/usr/bin/env bash
# Installer for DaVinci Resolve MCP (macOS/Linux).
#
# Creates a virtualenv next to the project, installs the package in
# editable mode, and prints next-step guidance.  The actual MCP server is
# launched by your MCP client via `python -m davinci_resolve_mcp` (or the
# `davinci-resolve-mcp` console script); see config/ for client templates.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_DIR="${VENV_DIR:-$PROJECT_ROOT/venv}"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  DaVinci Resolve MCP Installer${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Project root: $PROJECT_ROOT${NC}"
echo -e "${YELLOW}Virtualenv:   $VENV_DIR${NC}"
echo ""

if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}Error: python3 is required but not on PATH.${NC}" >&2
    exit 1
fi

PY_VERSION="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
PY_MAJOR="${PY_VERSION%%.*}"
PY_MINOR="${PY_VERSION##*.}"
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo -e "${RED}Error: Python 3.10+ is required (found $PY_VERSION).${NC}" >&2
    exit 1
fi
echo -e "${GREEN}✓ Python $PY_VERSION${NC}"

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating virtualenv...${NC}"
    python3 -m venv "$VENV_DIR"
fi
echo -e "${GREEN}✓ Virtualenv ready${NC}"

echo -e "${YELLOW}Installing davinci-resolve-mcp in editable mode...${NC}"
"$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
"$VENV_DIR/bin/pip" install -e "$PROJECT_ROOT"
echo -e "${GREEN}✓ Package installed${NC}"

cat <<EOF

${BLUE}Next steps:${NC}
  1. Ensure DaVinci Resolve is running, then verify with:
       $SCRIPT_DIR/../check-resolve-ready.sh

  2. Configure your MCP client (Cursor, Claude Desktop, etc.).
     Templates live under: $PROJECT_ROOT/config
     Use either of these launch commands in the template:
       command: $VENV_DIR/bin/python
       args:    ["-m", "davinci_resolve_mcp"]
     or the installed console script:
       command: $VENV_DIR/bin/davinci-resolve-mcp

  3. (Optional) The execute_python tool is gated for safety.  Set
     RESOLVE_MCP_ALLOW_EXEC=1 in the MCP client environment to enable it.

EOF
