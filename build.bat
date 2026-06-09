@echo off
REM Install dependencies
pip install -r requirements.txt

REM Run PyInstaller
pyinstaller --clean EyeGuardian.spec
    
echo Build complete. Executable is in the dist\ folder.
pause
