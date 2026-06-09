#!/bin/bash
# Configuration launcher for Eye & Posture Health App (Linux)

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to script directory
cd "$SCRIPT_DIR"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if not already installed
if ! python -c "import cv2" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the configuration GUI
echo "Launching Configuration GUI..."
python main_app.py config
