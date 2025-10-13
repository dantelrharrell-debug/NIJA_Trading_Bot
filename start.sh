#!/bin/bash
# Activate the venv
. .venv/bin/activate

# Optional debug info
echo "Python executable: $(which python3)"
echo "Pip packages installed:"
pip list | grep coin

# Start your bot
python3 nija_bot.py
