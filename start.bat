@echo off
REM Launcher script for Eye & Posture Health App (Windows)

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Change to script directory
cd /d "%SCRIPT_DIR%"

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies if not already installed
python -c "import cv2" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Run the application
echo Starting Eye & Posture Health App...
python main_app.py %*

pause
