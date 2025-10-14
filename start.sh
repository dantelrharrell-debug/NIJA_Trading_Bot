#!/bin/bash

# Explicitly activate the virtual environment
source "$PWD/.venv/bin/activate"

# Optional: upgrade pip just to be safe
python3 -m pip install --upgrade pip

# Ensure all packages from requirements.txt are installed
python3 -m pip install -r requirements.txt

# Run the bot
python3 nija_bot.py
