#!/bin/bash
# ========================
# START SCRIPT - NIJA BOT
# ========================

echo "🔄 Starting NIJA BOT..."

# Activate virtual environment if it exists
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

# Install requirements
if [ -f "requirements.txt" ]; then
    pip install --no-cache-dir -r requirements.txt
else
    echo "⚠️ requirements.txt not found. Installing essential packages..."
    pip install --no-cache-dir coinbase-advanced-py==1.8.2 python-dotenv flask gunicorn pandas numpy
fi

# Run the bot
echo "🚀 Running nija_bot.py..."
python3 nija_bot.py
