#!/bin/bash
# Render-safe start.sh for Nija bot

# 1️⃣ Create venv if missing
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# 2️⃣ Install dependencies (safe to skip if already installed)
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

# 3️⃣ Debug info
echo "🟢 Using Python:"
.venv/bin/python -V
echo "🟢 Checking coinbase_advanced_py..."
.venv/bin/python -m pip show coinbase-advanced-py

# 4️⃣ Run bot using the correct Python
echo "🚀 Starting Nija Trading Bot..."
exec .venv/bin/python nija_bot.py
