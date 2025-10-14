#!/bin/bash
# Activate the virtual environment FIRST
source .venv/bin/activate

# Optional: force reinstall to be 100% sure
pip install --force-reinstall coinbase-advanced-py==1.8.2

# Run your bot
python3 nija_bot.py
