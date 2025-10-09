#!/bin/bash
# start.sh

# Activate the virtual environment
source .venv/bin/activate

# Optional: Upgrade pip
python3 -m pip install --upgrade pip --break-system-packages

# Install dependencies if needed
python3 -m pip install -r requirements.txt --break-system-packages

# Run the bot using the venv python
python3 -u nija_bot.py
