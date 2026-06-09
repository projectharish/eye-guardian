#!/bin/bash
# Activate venv
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run PyInstaller
pyinstaller --clean EyeGuardian.spec
    
echo "Build complete. Executable is in the dist/ folder."
