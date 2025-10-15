#!/bin/bash
# start.sh — Render-safe virtualenv

# 1️⃣ Create or activate virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# 2️⃣ Upgrade pip and install dependencies using venv Python
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

# 3️⃣ Debug info
echo "🟢 Python being used:"
.venv/bin/python -V
.venv/bin/python -m pip show coinbase-advanced-py

# 4️⃣ Run the bot **explicitly using venv Python**
echo "🚀 Starting Nija Trading Bot..."
exec .venv/bin/python nija_bot.py
