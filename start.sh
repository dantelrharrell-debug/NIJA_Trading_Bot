#!/bin/bash
# start.sh — Render-safe virtualenv

# 1️⃣ Activate virtual environment
if [ -d ".venv" ]; then
    echo "🟢 Activating existing virtual environment..."
else
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

# 2️⃣ Install dependencies if missing
.venv/bin/python -m pip show coinbase-advanced-py > /dev/null || {
    echo "📦 Installing dependencies..."
    .venv/bin/python -m pip install --upgrade pip
    .venv/bin/python -m pip install -r requirements.txt
}

# 3️⃣ Debug info
echo "🟢 Using Python: $(.venv/bin/python -V)"
.venv/bin/python -m pip show coinbase-advanced-py

# 4️⃣ Run Nija bot explicitly using venv Python
echo "🚀 Starting Nija Trading Bot..."
exec .venv/bin/python nija_bot.py
