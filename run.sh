#!/bin/bash

# Ensure we are in the script's directory for error-free cron execution
cd "$(dirname "$0")"

# Securely initialize the virtual python environment if it does not already exist
if [ ! -d "venv" ]; then
    echo "First time setup: Creating environment and installing dependencies..."
    
    if ! command -v python3 &> /dev/null; then
        export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
    fi
    
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

# Execute the main script safely using the virtual environment
./venv/bin/python main.py "$@"
