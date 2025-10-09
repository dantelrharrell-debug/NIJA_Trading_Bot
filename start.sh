#!/usr/bin/env bash
set -e
set -o pipefail

echo "🚀 Starting Nija Trading Bot..."

# 1️⃣ Activate or create virtual environment
if [ -d ".venv" ]; then
    echo "🟢 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️ Virtual environment not found. Creating .venv..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# 2️⃣ Upgrade pip & install essentials
echo "📦 Upgrading pip and setuptools..."
python3 -m pip install --upgrade pip setuptools wheel

# 3️⃣ Run the bot
python3 nija_bot.py
