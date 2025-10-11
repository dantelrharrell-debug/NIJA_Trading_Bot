#!/bin/bash
set -e

# Activate the virtual environment
source .venv/bin/activate

# Optional: confirm Python path and packages
echo "Python being used: $(which python)"
python -m pip list | grep coinbase

# Run your bot
python nija_bot.py
