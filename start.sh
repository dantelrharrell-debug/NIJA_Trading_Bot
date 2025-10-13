#!/bin/bash

# -------------------------------
# start.sh for Render deployment
# -------------------------------

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    . .venv/bin/activate
else
    echo "❌ Virtual environment not found. Make sure .venv exists."
    exit 1
fi

# Optional: show Python info for debugging
echo "🚀 Using Python: $(which python3)"
echo "📦 Installed packages (coinbase_advanced_py):"
pip list | grep coin

# Run the bot
python3 nija_bot.py
