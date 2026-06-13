@echo off
REM Installer for DaVinci Resolve MCP (Windows).
REM
REM Creates a virtualenv next to the project, installs the package in
REM editable mode, and prints next-step guidance.  The actual MCP server
REM is launched by your MCP client via `python -m davinci_resolve_mcp`
REM (or the `davinci-resolve-mcp` console script); see config\ for client
REM templates.

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"
if not defined VENV_DIR set "VENV_DIR=%PROJECT_ROOT%\venv"

echo ===============================================================
echo   DaVinci Resolve MCP Installer
echo ===============================================================
echo Project root: %PROJECT_ROOT%
echo Virtualenv:   %VENV_DIR%
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo Error: python is required but not on PATH.
    exit /b 1
)

for /f "tokens=2 delims= " %%V in ('python --version 2^>^&1') do set "PY_VERSION=%%V"
for /f "tokens=1,2 delims=." %%A in ("%PY_VERSION%") do (
    set "PY_MAJOR=%%A"
    set "PY_MINOR=%%B"
)
if %PY_MAJOR% LSS 3 goto :pyver_fail
if %PY_MAJOR% EQU 3 if %PY_MINOR% LSS 10 goto :pyver_fail
echo [ OK ] Python %PY_VERSION%
goto :pyver_ok

:pyver_fail
echo Error: Python 3.10+ is required (found %PY_VERSION%).
exit /b 1

:pyver_ok
if not exist "%VENV_DIR%\" (
    echo Creating virtualenv...
    python -m venv "%VENV_DIR%"
)
echo [ OK ] Virtualenv ready

echo Installing davinci-resolve-mcp in editable mode...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip >nul
"%VENV_DIR%\Scripts\python.exe" -m pip install -e "%PROJECT_ROOT%"
if errorlevel 1 (
    echo Error: pip install failed.
    exit /b 1
)
echo [ OK ] Package installed

echo.
echo Next steps:
echo   1. Ensure DaVinci Resolve is running, then verify with:
echo        %SCRIPT_DIR%..\check-resolve-ready.bat
echo.
echo   2. Configure your MCP client (Cursor, Claude Desktop, etc.).
echo      Templates live under: %PROJECT_ROOT%\config
echo      Use either of these launch commands in the template:
echo        command: %VENV_DIR%\Scripts\python.exe
echo        args:    ["-m", "davinci_resolve_mcp"]
echo      or the installed console script:
echo        command: %VENV_DIR%\Scripts\davinci-resolve-mcp.exe
echo.
echo   3. (Optional) The execute_python tool is gated for safety.  Set
echo      RESOLVE_MCP_ALLOW_EXEC=1 in the MCP client environment to enable it.
echo.

endlocal
