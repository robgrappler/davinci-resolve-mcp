# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-06-20

### Changed
- **BREAKING**: All `@tool()` functions now return a uniform response envelope `{ok, data, error, message, context}` instead of raw strings or ad-hoc dicts. This enables pipeline-oriented clients to check `result["ok"]` and parse errors uniformly. See `docs/PHASE4_ENVELOPE_PLAN.md` for migration details.

### Added
- `warn_response()` helper in `utils/response.py` for soft no-op scenarios (e.g., "queue already empty")

## [Unreleased]

### Security
- The `execute_python` tool (arbitrary Python execution) is now disabled by default. Set `RESOLVE_MCP_ALLOW_EXEC=1` to opt in. The tool also executes code in an isolated namespace instead of the server module's globals.

### Fixed
- Replaced broken `run-now.sh` / `run-now.bat` symlinks at the repo root (they pointed to an absolute path on a maintainer's machine) with portable wrapper scripts that delegate to `scripts/`.
- Removed hardcoded user paths from `scripts/run-server.sh`; it now resolves paths relative to the script location.
- `examples/media/import_folder.py` now takes the source folder as a command-line argument instead of a hardcoded path.
- Removed a duplicate import block in `src/resolve_mcp_server.py`.

### Changed
- Consolidated three changelog files (`CHANGELOG.md`, `CHANGES.md`, `docs/CHANGELOG.md`) into this single root `CHANGELOG.md`.
- `requirements.txt`: removed the redundant `git+https` dependency on the MCP python-sdk repository (`mcp[cli]` on PyPI is the same package) and annotated dev/test-only dependencies.
- Removed the stale copy of `resolve_mcp_server.py` from `scripts/`.
- Documented the supported Python version as 3.10+ (required by the MCP SDK).

### Added
- `docs/AUDIT.md`: repository audit and phased improvement roadmap.

## [1.3.8] - 2025-04

### Changed
- **Cursor Integration**: Added comprehensive documentation for Cursor setup process
- **Entry Point**: Standardized on `main.py` as the proper entry point (replaces direct use of `resolve_mcp_server.py`)
- **Configuration Templates**: Updated example configuration files to use correct paths
- **Documentation**: Added detailed troubleshooting for "client closed" errors in Cursor

### Fixed
- Ensured consistent documentation for environment setup

## [1.3.7] - 2025-04

### Added
- Unified one-step installation: `install.sh` (macOS/Linux) and `install.bat` (Windows) with automatic validation and verification
- Installation verification scripts (`verify-installation.sh` / `verify-installation.bat`) covering the Python environment, MCP SDK, configuration files, and DaVinci Resolve status
- Comprehensive installation guide (`INSTALL.md`) with troubleshooting section
- Release packaging scripts with automatic version extraction from VERSION.md

### Changed
- Standardized directory structure: single root `venv/`, server moved to `src/`, configuration templates in `config/`, installation scripts in `scripts/setup/`, tests in `tests/`
- Scripts now resolve paths relative to their own location instead of assuming a directory structure
- Improved DaVinci Resolve process detection (more robust matching, retry with timeout)
- Configuration generation uses absolute paths and supports system-level and project-level configs

## [1.3.6] - 2025-03-29

### Added
- Comprehensive Feature Additions:
  - Complete MediaPoolItem functionality:
    - LinkProxyMedia/UnlinkProxyMedia for proxy media workflow
    - ReplaceClip functionality for swapping media files
    - TranscribeAudio/ClearTranscription for audio transcription
  - Complete Folder object methods:
    - Export functionality for DRB folder archives
    - TranscribeAudio for batch audio transcription
    - ClearTranscription for managing folder-level transcriptions
  - Cache Management implementation:
    - Get/set cache mode (auto, on, off)
    - Control optimized media settings
    - Manage proxy media settings including quality
    - Configure cache file paths (local/network)
    - Generate and delete optimized media for specific clips
  - Timeline Item Properties implementation:
    - Transform properties (position, scale, rotation, anchor point)
    - Crop controls (left, right, top, bottom)
    - Composite mode and opacity settings
    - Retime controls including speed and process type
    - Stabilization controls including method and strength
    - Audio properties including volume, pan, and EQ settings
  - Keyframe Control implementation:
    - Resource endpoint for retrieving all keyframes for timeline items
    - Add/modify/delete keyframe tools for precise animation control
    - Keyframe interpolation control (Linear, Bezier, Ease-In, Ease-Out)
    - Keyframe mode selection (All, Color, Sizing)
    - Support for all keyframeable properties (transform, crop, composite)
  - Color Preset Management implementation:
    - Resource endpoint for retrieving all color presets in albums
    - Save color presets from timeline clips with customizable naming
    - Apply color presets to timeline clips by ID or name
    - Delete color presets from albums
    - Create and manage color preset albums
  - LUT Export functionality:
    - Tool for exporting grades from clips as LUT files
    - Support for multiple LUT formats (Cube, DaVinci, 3DL, Panasonic)
    - Variable LUT sizing options (17-point, 33-point, 65-point)
    - Batch export functionality for PowerGrades
  - Added helper functions for recursively accessing media pool items
  - Updated FEATURES.md with comprehensive documentation

### Changed
- Project directory restructuring to better organize files:
  - Moved documentation files to `docs/` directory
  - Moved test scripts to `scripts/tests/` directory
  - Moved configuration templates to `config-templates/` directory
  - Moved utility scripts to `scripts/` directory
  - Updated all scripts to work with the new directory structure
  - Created simpler launcher scripts in the root directory
- Updated Implementation Progress Summary to reflect 100% completion of MediaPoolItem and Folder features
- Enhanced project documentation with better usage examples
- Improved media management functionality with expanded clip operations
- Enhanced timeline item handling with ID-based lookup
- Improved property validation with comprehensive error reporting
- Added support for both video and audio timeline item properties
- Enhanced color workflow efficiency with preset system
- Improved organization of saved grades with album management
- Enhanced cross-application compatibility with industry-standard LUT formats

## [1.3.5] - 2025-03-29

### Added
- Updated Cursor integration with new templating system
- Improved client-specific launcher scripts for better usability
- Added automatic Cursor MCP configuration generation
- Enhanced cross-platform compatibility in launcher scripts

### Changed
- Updated Cursor integration script to use project root relative paths
- Simplified launcher script by removing dependencies on intermediate scripts
- Improved virtual environment detection and validation

### Fixed
- Path handling in Cursor configuration for more reliable connections
- Virtual environment validation to prevent launch failures
- Environment variable checking with more robust validation

## [1.3.4] - 2025-03-28

### Changed
- Improved template configuration for MCP clients with better documentation
- Fixed Cursor integration templates to use direct Python path instead of MCP CLI
- Simplified configuration process by removing environment variable requirements
- Added clearer warnings in templates and README about path replacement
- Created VERSION.md file for easier version tracking

### Fixed
- Connection issues with Cursor MCP integration
- Path variable handling in configuration templates
- Configuration templates now use consistent variable naming

## [1.3.3] - 2025-03-27

### Fixed
- Improved Windows compatibility for the run-now.bat script:
  - Fixed ANSI color code syntax errors in Windows command prompt
  - Made the npm/Node.js check a warning instead of an error
  - Simplified environment variable handling for better Windows compatibility
  - Fixed command syntax in batch file for more reliable execution
  - Improved DaVinci Resolve process detection for Windows
  - Added support for detecting multiple possible DaVinci Resolve executable names
  - Enhanced batch file error handling and robustness
  - Fixed issue with running the MCP server executable on Windows
  - Increased timeout waiting for DaVinci Resolve to start
- Added Windows specific templates in config-templates

## [1.3.2] - 2025-03-28

### Added
- Experimental Windows support with platform-specific path detection
- Dynamic environment setup based on operating system
- Platform utility module for handling OS-specific paths and configurations
- Enhanced error messages with platform-specific environment setup instructions
- Windows pre-launch check script (PowerShell) with automatic environment configuration
- Windows batch file launcher for easy execution of the pre-launch check

### Changed
- Refactored path setup code to use platform detection
- Improved logging with platform-specific information
- Updated documentation to reflect Windows compatibility status
- Enhanced README with Windows-specific configuration instructions

### Fixed
- Platform-dependent path issues that prevented Windows compatibility
- Environment variable handling for cross-platform use
- Windows-specific configuration paths for Cursor integration

## [1.3.1] - 2025-03-27

### Added
- Universal launcher script (`mcp_resolve_launcher.sh`) that provides both interactive and command-line interfaces for:
  - Starting and stopping Cursor MCP server
  - Starting and stopping Claude Desktop MCP server
  - Running both servers simultaneously
  - Checking server status
  - Forcing server start even if DaVinci Resolve isn't detected
  - Specifying a project to open on server start
- Improved Claude Desktop integration script with better error handling and force mode
- Enhanced detection for running DaVinci Resolve process

### Changed
- Updated documentation to include new universal launcher functionality
- Improved server startup process with better error handling and logging
- Enhanced cross-client compatibility between Cursor and Claude Desktop
- Relocated and improved marker test script from root to examples/markers directory with better documentation and organization

### Fixed
- Process detection issues when looking for running DaVinci Resolve
- Signal handling in server scripts for cleaner termination

## [1.3.0] - 2025-03-26

### Added
- Support for adding clips to timeline directly by name
- Intelligent marker placement with frame detection
- Enhanced logging and error reporting
- Improved code organization with modular architecture

### Changed
- Reorganized project structure for better maintainability
- Enhanced Claude Desktop integration with better error handling
- Optimized connection to DaVinci Resolve for faster response times
- Updated documentation to include more examples

### Fixed
- Issues with marker placement on empty timelines
- Media pool navigation in complex project structures
- Timing issues when rapidly sending commands to DaVinci Resolve

## [1.1.0] - 2025-03-26

### Added
- Claude Desktop integration with claude_desktop_config.json support
- Consolidated server management script (scripts/server.sh)
- Project structure reorganization for better maintenance
- Configuration templates for easier setup

### Changed
- Moved scripts to dedicated scripts/ directory
- Organized example files into examples/ directory
- Updated README with Claude Desktop instructions
- Updated FEATURES.md to reflect Claude Desktop compatibility

### Fixed
- Environment variable handling in server scripts
- Path references in documentation

## [1.0.0] - 2025-03-24

### Added
- Initial release with Cursor integration
- DaVinci Resolve connection functionality
- Project management features (list, open, create projects)
- Timeline operations (create, list, switch timelines)
- Marker functionality with advanced frame detection
- Media Pool operations (import media, create bins)
- Comprehensive setup scripts
- Pre-launch check script

### Changed
- Switched from original MCP framework to direct JSON-RPC for improved reliability

### Fixed
- Save Project functionality with multi-method approach
- Environment variable setup for consistent connection

## [0.3.1] - 2025-03-27

### Changed
- Completely overhauled marker functionality:
  - Added intelligent frame selection when frame is not specified
  - Improved error handling for marker placement
  - Added collision detection to avoid overwriting existing markers
  - Added suggestions for alternate frames when a marker already exists
  - Implemented validation to ensure markers are placed on actual clips
  - Better debugging and detailed error messages

### Fixed
- Resolved issue with markers failing silently when trying to place on invalid frames
- Fixed marker placement to only allow adding markers on actual media content

## [0.3.0] - 2025-03-26

### Added
- Implemented "Add Clip to Timeline" feature to allow adding media pool clips to timelines
- Added test script for validating timeline operations
- Added comprehensive marker testing to improve functionality

### Changed
- Cleaned up project structure by removing redundant test scripts and log files
- Removed duplicate server implementations to focus on the main MCP server
- Consolidated server startup scripts to simplify usage
- Created backup directories for removed files (cleanup_backup and logs_backup)
- Improved marker functionality with better frame detection and clip-aware positioning

## [0.2.0] - 2025-03-25

### Added
- Added new features and improvements
- Updated documentation

## [0.1.0] - 2025-03-26

### Added
- Initial release with core functionality
- Connection to DaVinci Resolve via MCP
- Project management features (list, open, create projects)
- Timeline operations (list, create, switch timelines, add markers)
- Media pool operations (list clips, import media, create bins)
- Setup script for easier installation and configuration
- Comprehensive documentation
