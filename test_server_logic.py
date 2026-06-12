import os
import sys
import logging
from pathlib import Path

# Add project root to sys.path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

# Mock MCP for testing initialization
class MockMCP:
    def tool(self): return lambda f: f
    def resource(self, path): return lambda f: f

# Setup environment like mcp_config.json
paths = {
    "api_path": "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting",
    "lib_path": "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so",
    "modules_path": "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"
}
os.environ["RESOLVE_SCRIPT_API"] = paths["api_path"]
os.environ["RESOLVE_SCRIPT_LIB"] = paths["lib_path"]
if paths["modules_path"] not in sys.path:
    sys.path.insert(0, paths["modules_path"])

# Configure logging to stdout so we can see it
logging.basicConfig(level=logging.INFO)

def test_server_init():
    try:
        from src.resolve_mcp_server import get_resolve
        print("Imported get_resolve")
        resolve = get_resolve()
        if resolve:
            print(f"Server successfully connected to Resolve: {resolve.GetProductName()}")
        else:
            print("Server failed to connect to Resolve.")
    except Exception as e:
        print(f"Exception during server initialization test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_server_init()
