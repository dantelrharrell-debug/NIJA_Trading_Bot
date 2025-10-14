#!/bin/bash

# Activate virtual environment
source "$PWD/.venv/bin/activate"

# Upgrade pip safely
python3 -m pip install --upgrade pip

# Install dependencies
python3 -m pip install -r requirements.txt

echo "🚀 Starting Nija bot with auto-restart..."

# Infinite loop to keep the bot running
while true; do
    echo "🔁 Launching bot..."
    python3 nija_bot.py   # <-- Run your bot file directly
    echo "⚠️ Bot exited unexpectedly, restarting in 5 seconds..."
    sleep 5
done
