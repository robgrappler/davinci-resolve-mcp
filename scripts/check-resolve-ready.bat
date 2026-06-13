@echo off
REM Pre-launch checks for DaVinci Resolve MCP (Windows).
REM
REM Verifies:
REM   1. DaVinci Resolve process is running.
REM   2. RESOLVE_SCRIPT_API / RESOLVE_SCRIPT_LIB env vars point at real paths.
REM   3. davinci_resolve_mcp package is importable.

setlocal enabledelayedexpansion

set "status=0"

echo ===============================================================
echo   DaVinci Resolve MCP Pre-Launch Check
echo ===============================================================

REM 1. DaVinci Resolve running
tasklist /FI "IMAGENAME eq Resolve.exe" 2>nul | find /I "Resolve.exe" >nul
if errorlevel 1 (
    echo [FAIL] DaVinci Resolve is not running -- start it before launching the MCP server.
    set "status=1"
) else (
    echo [ OK ] DaVinci Resolve is running
)

REM 2. Environment variables
set "default_api=C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
set "default_lib=C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"

if not defined RESOLVE_SCRIPT_API set "RESOLVE_SCRIPT_API=%default_api%"
if not defined RESOLVE_SCRIPT_LIB set "RESOLVE_SCRIPT_LIB=%default_lib%"

if exist "%RESOLVE_SCRIPT_API%\" (
    echo [ OK ] RESOLVE_SCRIPT_API = %RESOLVE_SCRIPT_API%
) else (
    echo [FAIL] RESOLVE_SCRIPT_API not set or path missing: %RESOLVE_SCRIPT_API%
    set "status=1"
)

if exist "%RESOLVE_SCRIPT_LIB%" (
    echo [ OK ] RESOLVE_SCRIPT_LIB = %RESOLVE_SCRIPT_LIB%
) else (
    echo [FAIL] RESOLVE_SCRIPT_LIB not set or file missing: %RESOLVE_SCRIPT_LIB%
    set "status=1"
)

REM 3. Package importable
where python >nul 2>&1
if errorlevel 1 (
    echo [FAIL] python not found on PATH
    set "status=1"
) else (
    python -c "import davinci_resolve_mcp" >nul 2>&1
    if errorlevel 1 (
        echo [FAIL] davinci_resolve_mcp not installed. Run: pip install -e .
        set "status=1"
    ) else (
        echo [ OK ] davinci_resolve_mcp package importable
    )
)

echo.
if "%status%"=="0" (
    echo [ OK ] All checks passed. Configure your MCP client to launch: python -m davinci_resolve_mcp
) else (
    echo [WARN] One or more checks failed. See messages above.
)

endlocal ^& exit /b %status%
