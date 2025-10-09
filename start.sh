#!/bin/bash
# Render-ready start script for NIJA Trading Bot

# Exit immediately if a command fails
set -e

echo "🚀 Starting NIJA Trading Bot..."

# 1. Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# 2. Upgrade pip in venv
python3 -m pip install --upgrade pip --break-system-packages

# 3. Install requirements
python3 -m pip install --break-system-packages -r requirements.txt

# 4. Run the bot
python3 -u nija_bot.py
