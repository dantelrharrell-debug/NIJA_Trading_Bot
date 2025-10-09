#!/bin/bash
# start.sh — Render-friendly

# Make sure we use venv python
source .venv/bin/activate

# Upgrade pip (optional)
python3 -m pip install --upgrade pip --break-system-packages

# Install dependencies if not already installed
python3 -m pip install -r requirements.txt --break-system-packages

# Run the bot using venv python
python3 -u nija_bot.py
