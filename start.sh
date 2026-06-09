#!/bin/bash
# Launcher script for Eye & Posture Health App (Linux)

# Get the directory where this script is located
export SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to script directory
cd "$SCRIPT_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    notify-send "Eye Guardian" "Error: Python 3 is not installed."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    # Activate virtual environment
    source venv/bin/activate
fi

# Ensure dependencies are installed (quick check)
if ! python3 -c "import cv2" 2>/dev/null; then
    echo "Installing missing dependencies..."
    pip install -r requirements.txt
fi

# Run the application
echo "Starting Eye Guardian Dashboard from $SCRIPT_DIR..."
python3 main_gui.py "$@"
