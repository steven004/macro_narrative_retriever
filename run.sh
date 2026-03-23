#!/bin/bash

# Ensure we are in the script's directory for error-free cron execution
cd "$(dirname "$0")"

# Securely initialize the virtual python environment if it does not already exist
if [ ! -f "venv/bin/activate" ] && [ ! -f "venv/Scripts/activate" ]; then
    echo "First time setup: Creating environment and installing dependencies..."
    
    # Remove broken venv if it exists
    rm -rf venv
    
    if ! command -v python3 &> /dev/null; then
        export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo "Error: python3 could not be found. Please install Python 3."
        exit 1
    fi
    
    python3 -m venv venv || { echo "Error: Failed to create virtual environment"; exit 1; }
    
    # Cross-platform install
    if [ -f "venv/bin/pip3" ]; then
        ./venv/bin/pip3 install -r requirements.txt || { echo "Error: Failed to install requirements"; exit 1; }
    elif [ -f "venv/Scripts/pip" ]; then
        ./venv/Scripts/pip install -r requirements.txt || { echo "Error: Failed to install requirements"; exit 1; }
    elif [ -f "venv/bin/pip" ]; then
        ./venv/bin/pip install -r requirements.txt || { echo "Error: Failed to install requirements"; exit 1; }
    else
        echo "Error: pip not found inside virtual environment."
        exit 1
    fi
fi

# Execute the main script safely using the direct virtual environment binary
if [ -f "venv/bin/python3" ]; then
    ./venv/bin/python3 main.py "$@"
elif [ -f "venv/Scripts/python" ]; then
    ./venv/Scripts/python main.py "$@"
elif [ -f "venv/bin/python" ]; then
    ./venv/bin/python main.py "$@"
else
    echo "Error: Python executable not found in virtual environment."
    exit 1
fi
