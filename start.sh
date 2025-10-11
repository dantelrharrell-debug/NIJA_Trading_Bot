#!/bin/bash
# start.sh for Nija bot on Render

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting Nija bot setup..."

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "✅ Activating virtual environment"
    source .venv/bin/activate
else
    echo "⚠️ .venv not found, creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing requirements..."
pip install -r requirements.txt

# Ensure coinbase_advanced_py is installed
pip install coinbase-advanced-py==1.8.2

# Run the bot
echo "🤖 Running nija_bot.py..."
python3 nija_bot.py
