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

REM 3. Package importable -- prefer the project venv created by install.bat,
REM fall back to whatever python is on PATH.
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "VENV_PYTHON=%PROJECT_ROOT%\venv\Scripts\python.exe"

set "py="
if exist "%VENV_PYTHON%" (
    set "py=%VENV_PYTHON%"
) else (
    where python >nul 2>&1
    if not errorlevel 1 set "py=python"
)

if not defined py (
    echo [FAIL] No python interpreter found
    set "status=1"
) else (
    "%py%" -c "import davinci_resolve_mcp" >nul 2>&1
    if errorlevel 1 (
        echo [FAIL] davinci_resolve_mcp not installed in %py%. Run: scripts\setup\install.bat
        set "status=1"
    ) else (
        echo [ OK ] davinci_resolve_mcp package importable ^(%py%^)
    )
)

echo.
if "%status%"=="0" (
    echo [ OK ] All checks passed. Configure your MCP client to launch: "%py%" -m davinci_resolve_mcp
) else (
    echo [WARN] One or more checks failed. See messages above.
)

endlocal ^& exit /b %status%
