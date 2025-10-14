#!/bin/bash
# -------------------------------
# start.sh for Nija Bot on Render
# -------------------------------

# Exit immediately if a command fails
set -e

# Activate the virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "❌ Virtual environment not found! Aborting."
    exit 1
fi

# Optional: upgrade pip (safe to keep)
pip install --upgrade pip

# Optional: force reinstall Coinbase package to avoid ModuleNotFoundError
pip install --no-cache-dir coinbase-advanced-py==1.8.2

# Launch the bot
echo "🚀 Launching Nija bot..."
python nija_bot.py
