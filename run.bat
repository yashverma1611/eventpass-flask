@echo off
title EventPass Flask Platform Launcher
color 0a
cd /d "%~dp0"

echo =========================================================
echo       Starting EventPass (Python Flask 3.0 Platform)
echo =========================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your system PATH!
    echo.
    echo To fix this:
    echo   1. Install Python 3.12 (Check "Add Python to PATH" during installation)
    echo   2. Or run setup_environment.bat in the parent directory.
    echo   3. Or double-click demo\index.html to view the instant working demo in your browser!
    echo.
    start "" "demo\index.html"
    pause
    exit /b
)

echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo Initializing SQLite database and sample events...
python seed_data.py

echo Starting Flask server on http://localhost:5000...
start "" "http://localhost:5000"
python run.py
pause
