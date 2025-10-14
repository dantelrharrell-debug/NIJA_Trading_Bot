#!/bin/bash

echo "🔄 Starting NIJA BOT..."

# Create virtual environment if missing
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate
echo "✅ Virtual environment activated."

# Upgrade pip
python3 -m pip install --upgrade pip

# Install all requirements
pip install --no-cache-dir -r requirements.txt

# Run the bot
echo "🚀 Running nija_bot.py..."
python3 nija_bot.py
