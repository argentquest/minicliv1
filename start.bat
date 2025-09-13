@echo off
REM Code Chat AI - Startup Launcher Batch File
REM This batch file launches the interactive startcommands launcher

echo.
echo ===========================================
echo   🤖 Code Chat AI - Startup Launcher
echo ===========================================
echo.

REM Check if we're in the right directory
if not exist "startcommands" (
    echo ❌ Error: startcommands directory not found!
    echo Please run this batch file from the project root directory.
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo ✅ Found virtual environment
    echo.
    call venv\Scripts\activate.bat
) else if exist "Scripts\activate.bat" (
    echo ✅ Found virtual environment (Scripts folder)
    echo.
    call Scripts\activate.bat
) else (
    echo ⚠️  Warning: Virtual environment not found
    echo Attempting to run with system Python...
    echo.
)

REM Launch the startcommands launcher
echo 🚀 Starting Code Chat AI launcher...
echo.
python -m startcommands

REM If we get here, the launcher exited
echo.
echo 👋 Launcher closed. Press any key to exit...
pause >nul