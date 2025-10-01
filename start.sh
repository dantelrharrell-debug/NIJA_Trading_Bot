#!/bin/bash

# Activate virtual environment (Render auto-creates venv if you use pip install -r)
source ./venv/bin/activate || echo "venv not found, continuing..."

# Upgrade pip just in case
pip install --upgrade pip

# Make sure dependencies are installed
pip install -r requirements.txt

# Run the bot
python3 main.py
