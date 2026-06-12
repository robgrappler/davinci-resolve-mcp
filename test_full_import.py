import sys
import os
from pathlib import Path

# Add project root to sys.path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

def test_import():
    try:
        print("Attempting to import mcp from src.resolve_mcp_server...")
        from src.resolve_mcp_server import mcp
        print("Successfully imported mcp!")
        print(f"Tools registered: {[t.name for t in mcp._tools]}")
    except Exception as e:
        print(f"Failed to import mcp: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_import()
