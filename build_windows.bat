@echo off
echo ===================================================
echo   EyeGuardian Windows Build Script
echo   Builds a standalone EXE with Python embedded
echo   (No Python needed on the target machine!)
echo ===================================================
echo.

REM Check for Python (needed only on the BUILD machine)
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed on this build machine.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [1/5] Installing build dependencies...
pip install -r requirements.txt
pip install pyinstaller Pillow

echo [2/5] Downloading face landmarker model...
python download_models.py

echo [3/5] Converting icon to Windows format...
python convert_icon.py

echo [4/5] Building standalone EYE with PyInstaller...
echo       (This embeds Python + all libraries into a single EXE)
pyinstaller --clean EyeGuardian.spec

echo.
if exist "dist\EyeGuardian.exe" (
    echo ===================================================
    echo   BUILD SUCCESSFUL!
    echo ===================================================
    echo.
    echo   Standalone EXE: dist\EyeGuardian.exe
    echo   (Python is EMBEDDED - users don't need Python!)
    echo.
    echo [5/5] Creating installer...
    
    REM Check if Inno Setup is installed
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
        if exist "dist\EyeGuardianSetup.exe" (
            echo.
            echo   Installer created: dist\EyeGuardianSetup.exe
            echo   Share this file - it handles everything!
        ) else (
            echo   WARNING: Installer build failed.
        )
    ) else (
        echo   SKIPPED: Inno Setup 6 not found.
        echo   To create an installer:
        echo   1. Download Inno Setup from https://jrsoftware.org/isdl.php
        echo   2. Install it, then re-run this script
        echo   OR right-click installer.iss and select "Compile"
    )
) else (
    echo ===================================================
    echo   BUILD FAILED!
    echo ===================================================
    echo   EyeGuardian.exe was not created.
    echo   Check the error messages above.
)
echo.
pause
