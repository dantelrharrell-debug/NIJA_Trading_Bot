#!/bin/bash
# Activate virtual environment
. .venv/bin/activate

# Optional: show Python version and pip packages (debug info)
echo "Python version: $(python3 --version)"
echo "Installed packages:"
pip list

# Start your bot
python3 nija_bot.py
