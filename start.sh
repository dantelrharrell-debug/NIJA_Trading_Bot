#!/bin/bash

echo "🔄 Starting NIJA BOT..."

# Create/activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated."
else
    echo "⚠️ No virtual environment found. Creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Upgrade pip
python3 -m pip install --upgrade pip

# Install essential packages
pip install --no-cache-dir -r requirements.txt || \
pip install --no-cache-dir coinbase-advanced-py==1.8.2 python-dotenv flask gunicorn pandas numpy

# Run the bot
echo "🚀 Running nija_bot.py..."
python3 nija_bot.py
