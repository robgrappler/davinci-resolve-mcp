import os
import sys
import platform

def get_resolve_paths():
    system = platform.system().lower()
    if system == 'darwin':
        api_path = "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
        lib_path = "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
        modules_path = os.path.join(api_path, "Modules")
    return {"api_path": api_path, "lib_path": lib_path, "modules_path": modules_path}

def test_connection():
    paths = get_resolve_paths()
    os.environ["RESOLVE_SCRIPT_API"] = paths["api_path"]
    os.environ["RESOLVE_SCRIPT_LIB"] = paths["lib_path"]
    
    if paths["modules_path"] not in sys.path:
        sys.path.insert(0, paths["modules_path"])
        
    print(f"PYTHONPATH: {sys.path}")
    print(f"RESOLVE_SCRIPT_API: {os.environ.get('RESOLVE_SCRIPT_API')}")
    print(f"RESOLVE_SCRIPT_LIB: {os.environ.get('RESOLVE_SCRIPT_LIB')}")
    
    try:
        import DaVinciResolveScript as dvr_script
        print("Successfully imported DaVinciResolveScript")
        resolve = dvr_script.scriptapp("Resolve")
        if resolve:
            print(f"Successfully connected to Resolve: {resolve.GetProductName()} {resolve.GetVersionString()}")
        else:
            print("Failed to get Resolve object. scriptapp('Resolve') returned None.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()
