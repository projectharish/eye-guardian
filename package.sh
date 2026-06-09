#!/bin/bash
# Packaging script for Eye Guardian (Linux)

echo "Building Eye Guardian standalone executable..."

# Check for pyinstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing pyinstaller..."
    pip install pyinstaller
fi

# Clean previous builds
rm -rf build dist

# Run PyInstaller
pyinstaller --clean EyeGuardian.spec

echo "Build complete! Executable is in the dist/ folder."
