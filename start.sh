#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Activate virtual environment if it exists
if [ -d "./venv" ]; then
    source ./venv/bin/activate
else
    # Create virtual environment if missing
    python3 -m venv venv
    source ./venv/bin/activate
fi

# Upgrade pip to latest version
pip install --upgrade pip

# Install required dependencies
pip install -r requirements.txt

# Run the bot
python3 main.py
