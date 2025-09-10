@echo off
echo Starting Code Chat with AI...
cd /d "%~dp0"
python minicli.py
if %ERRORLEVEL% neq 0 (
    echo Error occurred. Press any key to exit...
    pause >nul
)