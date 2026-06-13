#!/bin/bash
# Pre-launch Check Script for DaVinci Resolve MCP
# This script verifies that DaVinci Resolve is running and all required components are installed
# before launching Cursor

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"
VENV_DIR="$SCRIPT_DIR/venv"
CURSOR_CONFIG_FILE="$HOME/.cursor/mcp.json"
RESOLVE_MCP_SERVER="$PROJECT_ROOT/src/resolve_mcp_server.py"

# Required files and their permissions
REQUIRED_FILES=(
    "$RESOLVE_MCP_SERVER:755"
    "$SCRIPT_DIR/run-now.sh:755"
    "$SCRIPT_DIR/setup.sh:755"
)

# Function to check if DaVinci Resolve is running
check_resolve_running() {
    # Look for the actual process name "Resolve" (not "DaVinci Resolve")
    if pgrep -x "Resolve" > /dev/null; then
        return 0 # Running
    else
        return 1 # Not running
    fi
}

# Function to check environment variables
check_resolve_env() {
    if [ -z "$RESOLVE_SCRIPT_API" ] || [ -z "$RESOLVE_SCRIPT_LIB" ]; then
        return 1 # Not set
    else
        return 0 # Set
    fi
}

# Function to check if the virtual environment exists and has MCP installed
check_venv() {
    if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/python" ]; then
        return 1 # Missing
    fi
    
    if ! "$VENV_DIR/bin/pip" list | grep -q "mcp"; then
        return 2 # Missing MCP
    fi
    
    return 0 # All good
}

# Function to check all required files and permissions
check_required_files() {
    local missing_files=()
    local wrong_permissions=()
    
    for req in "${REQUIRED_FILES[@]}"; do
        IFS=':' read -r file perm <<< "$req"
        
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        elif [ "$(stat -f '%A' "$file")" != "$perm" ]; then
            wrong_permissions+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        echo -e "${RED}✗ Missing required files:${NC}"
        for file in "${missing_files[@]}"; do
            echo -e "  - $file"
        done
        return 1
    fi
    
    if [ ${#wrong_permissions[@]} -gt 0 ]; then
        echo -e "${YELLOW}⚠ Some files have incorrect permissions:${NC}"
        for file in "${wrong_permissions[@]}"; do
            echo -e "  - $file"
        done
        return 2
    fi
    
    return 0
}

# Function to check if cursor config is properly set
check_cursor_config() {
    if [ ! -f "$CURSOR_CONFIG_FILE" ]; then
        return 1 # Missing
    fi
    
    if ! grep -q "davinci-resolve" "$CURSOR_CONFIG_FILE"; then
        return 2 # Missing config
    fi
    
    return 0 # All good
}

# Print header
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  DaVinci Resolve MCP Pre-Launch Check                        ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check 0: Required files and scripts
echo -e "${YELLOW}Checking required files and scripts...${NC}"
files_status=$(check_required_files)
file_check_result=$?

if [ "$file_check_result" -eq 0 ]; then
    echo -e "${GREEN}✓ All required files are present with correct permissions${NC}"
elif [ "$file_check_result" -eq 2 ]; then
    echo -e "${YELLOW}Fixing file permissions...${NC}"
    for req in "${REQUIRED_FILES[@]}"; do
        IFS=':' read -r file perm <<< "$req"
        if [ -f "$file" ]; then
            chmod "$perm" "$file"
            echo -e "  - Fixed permissions for $file"
        fi
    done
    echo -e "${GREEN}✓ File permissions fixed${NC}"
else
    echo -e "${RED}✗ Some required files are missing${NC}"
    echo -e "${YELLOW}Your checkout looks incomplete. Re-clone or pull the repo and try again.${NC}"
    echo -e "${YELLOW}Expected server at: $RESOLVE_MCP_SERVER${NC}"
    exit 1
fi

# Check 1: Is DaVinci Resolve running?
echo -e "${YELLOW}Checking if DaVinci Resolve is running...${NC}"
if check_resolve_running; then
    echo -e "${GREEN}✓ DaVinci Resolve is running${NC}"
else
    echo -e "${RED}✗ DaVinci Resolve is NOT running${NC}"
    echo -e "${YELLOW}Please start DaVinci Resolve before launching Cursor${NC}"
    
    # Ask if user wants to start DaVinci Resolve
    read -p "Would you like to start DaVinci Resolve now? (y/n): " start_resolve
    if [[ "$start_resolve" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Starting DaVinci Resolve...${NC}"
        open -a "DaVinci Resolve"
        echo -e "${YELLOW}Waiting for DaVinci Resolve to start...${NC}"
        sleep 5
        
        # Check again
        if check_resolve_running; then
            echo -e "${GREEN}✓ DaVinci Resolve started successfully${NC}"
        else
            echo -e "${YELLOW}DaVinci Resolve is starting. Please wait until it's fully loaded before proceeding.${NC}"
        fi
    else
        echo -e "${RED}DaVinci Resolve must be running for the MCP server to function properly.${NC}"
        exit 1
    fi
fi

# Check 2: Environment variables
echo -e "${YELLOW}Checking Resolve environment variables...${NC}"
if check_resolve_env; then
    echo -e "${GREEN}✓ Resolve environment variables are set${NC}"
    echo -e "  RESOLVE_SCRIPT_API = $RESOLVE_SCRIPT_API"
    echo -e "  RESOLVE_SCRIPT_LIB = $RESOLVE_SCRIPT_LIB"
else
    echo -e "${RED}✗ Resolve environment variables are NOT set${NC}"
    echo -e "${YELLOW}Setting default environment variables...${NC}"
    
    # Set default paths for macOS
    export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
    export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
    export PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
    
    echo -e "${GREEN}✓ Environment variables set for this session:${NC}"
    echo -e "  RESOLVE_SCRIPT_API = $RESOLVE_SCRIPT_API"
    echo -e "  RESOLVE_SCRIPT_LIB = $RESOLVE_SCRIPT_LIB"
    echo -e "${YELLOW}Note: These variables are only set for this session. For permanent setup, run ./setup.sh${NC}"
fi

# Check 3: Virtual environment
echo -e "${YELLOW}Checking Python virtual environment...${NC}"
venv_status=$(check_venv)
if [ "$venv_status" -eq 0 ]; then
    echo -e "${GREEN}✓ Virtual environment is set up correctly with MCP installed${NC}"
elif [ "$venv_status" -eq 2 ]; then
    echo -e "${RED}✗ MCP is not installed in the virtual environment${NC}"
    echo -e "${YELLOW}Installing MCP...${NC}"
    "$VENV_DIR/bin/pip" install mcp[cli]
    echo -e "${GREEN}✓ MCP installed${NC}"
else
    echo -e "${RED}✗ Virtual environment is missing or incomplete${NC}"
    echo -e "${YELLOW}Setting up virtual environment...${NC}"
    
    # Create virtual environment
    python3 -m venv "$VENV_DIR"
    
    # Install MCP
    "$VENV_DIR/bin/pip" install mcp[cli]
    
    echo -e "${GREEN}✓ Virtual environment created and MCP installed${NC}"
fi

# Check 4: Cursor configuration
echo -e "${YELLOW}Checking Cursor configuration...${NC}"
cursor_status=$(check_cursor_config)
if [ "$cursor_status" -eq 0 ]; then
    echo -e "${GREEN}✓ Cursor is configured to use the DaVinci Resolve MCP server${NC}"
elif [ "$cursor_status" -eq 1 ]; then
    echo -e "${RED}✗ Cursor configuration file is missing${NC}"
    echo -e "${YELLOW}Creating Cursor configuration...${NC}"
    
    # Create directory if it doesn't exist
    mkdir -p "$HOME/.cursor"
    
    # Create config file
    cat > "$CURSOR_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "davinci-resolve": {
      "name": "DaVinci Resolve MCP",
      "command": "$VENV_DIR/bin/python",
      "args": ["$SCRIPT_DIR/../src/main.py"]
    }
  }
}
EOF
    echo -e "${GREEN}✓ Cursor configuration created${NC}"
else
    echo -e "${RED}✗ Cursor configuration is missing DaVinci Resolve MCP settings${NC}"
    echo -e "${YELLOW}Updating Cursor configuration...${NC}"
    
    # Backup existing config
    cp "$CURSOR_CONFIG_FILE" "$CURSOR_CONFIG_FILE.bak"
    
    # Update config file - this is a simple approach that assumes the file is valid JSON
    # A more robust approach would use jq if available
    if grep -q "\"mcpServers\"" "$CURSOR_CONFIG_FILE"; then
        # mcpServers already exists, try to add our server
        sed -i '' -e 's/"mcpServers": {/"mcpServers": {\n    "davinci-resolve": {\n      "name": "DaVinci Resolve MCP",\n      "command": "'"$VENV_DIR\/bin\/python"'",\n      "args": ["'"$SCRIPT_DIR/../src/main.py"'"]\n    },/g' "$CURSOR_CONFIG_FILE"
    else
        # No mcpServers exists, create everything
        cat > "$CURSOR_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "davinci-resolve": {
      "name": "DaVinci Resolve MCP",
      "command": "$VENV_DIR/bin/python",
      "args": ["$SCRIPT_DIR/../src/main.py"]
    }
  }
}
EOF
    fi
    
    echo -e "${GREEN}✓ Cursor configuration updated${NC}"
fi

# Final message
echo ""
echo -e "${GREEN}All checks complete!${NC}"
echo -e "${GREEN}Your system is ready to use DaVinci Resolve with Cursor.${NC}"
echo ""

# Ask if user wants to launch Cursor
read -p "Would you like to launch Cursor now? (y/n): " launch_cursor
if [[ "$launch_cursor" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Launching Cursor...${NC}"
    open -a "Cursor"
    echo -e "${GREEN}Cursor launched. Enjoy using DaVinci Resolve with AI assistance!${NC}"
fi

exit 0 