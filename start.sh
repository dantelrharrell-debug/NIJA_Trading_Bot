#!/usr/bin/env bash
echo "🔹 Activating virtual environment..."
source .venv/bin/activate
echo "Python executable: $(which python3)"
echo "🔹 Starting NIJA Bot..."

# Run in LIVE mode
export USE_MOCK=False

python3 nija_bot.py
