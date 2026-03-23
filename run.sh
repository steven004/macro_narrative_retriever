#!/bin/bash

# Ensure we are in the script's directory for error-free cron execution
cd "$(dirname "$0")"

# Securely initialize the virtual python environment if it does not already exist
if [ ! -d "venv" ]; then
    echo "First time setup: Creating environment and installing dependencies..."
    
    if ! command -v python3 &> /dev/null; then
        export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo "Error: python3 could not be found. Please install Python 3."
        exit 1
    fi
    
    python3 -m venv venv || { echo "Error: Failed to create virtual environment"; exit 1; }
    ./venv/bin/pip install -r requirements.txt || { echo "Error: Failed to install requirements"; exit 1; }
fi

# Execute the main script safely using the virtual environment
./venv/bin/python main.py "$@"
