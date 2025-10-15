#!/bin/bash

VENV_DIR=".venv"

# 1️⃣ Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

# 2️⃣ Activate venv
source "$VENV_DIR/bin/activate"

# 3️⃣ Upgrade pip & install deps if missing
pip install --upgrade pip
pip install -r requirements.txt

# 4️⃣ Debug info
echo "🟢 Using Python:"
python -V
echo "🟢 Checking coinbase_advanced_py..."
pip show coinbase-advanced-py || echo "❌ coinbase_advanced_py not found!"

# 5️⃣ Run bot
echo "🚀 Starting Nija Trading Bot..."
python nija_bot.py
