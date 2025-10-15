#!/bin/bash
# Render-safe start.sh for Nija bot

VENV_DIR=".venv"

# 1️⃣ Create virtual environment if missing
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

# 2️⃣ Activate the virtual environment
source "$VENV_DIR/bin/activate"

# 3️⃣ Upgrade pip & install dependencies if missing
pip install --upgrade pip
pip install -r requirements.txt

# 4️⃣ Debug info
echo "🟢 Using Python:"
which python
python -V
echo "🟢 Checking coinbase_advanced_py..."
pip show coinbase-advanced-py || echo "❌ coinbase_advanced_py not found!"

# 5️⃣ Run bot
echo "🚀 Starting Nija Trading Bot..."
exec python nija_bot.py

exec .venv/bin/python nija_bot.py
