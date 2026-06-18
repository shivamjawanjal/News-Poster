@echo off
REM Install script for News Post Generator Desktop App

echo ========================================
echo News Post Generator - Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements-desktop.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Next steps:
echo 1. Create a .env file with your API keys:
echo    NEWS_API_KEY=your_key_here
echo    GEMINI_API_KEY=your_key_here
echo.
echo 2. Run the app:
echo    python desktop_app.py
echo.
echo Or create a shortcut with:
echo    pythonw.exe desktop_app.py
echo.
pause
