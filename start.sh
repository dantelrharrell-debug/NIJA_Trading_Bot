#!/bin/bash
# Render-optimized start.sh for Nija Trading Bot

# 1️⃣ Set paths
VENV_DIR=".venv"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

# 2️⃣ Create virtual environment if missing
if [ ! -d "$VENV_DIR" ]; then
    echo "🟢 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# 3️⃣ Upgrade pip in venv
echo "🟢 Upgrading pip..."
"$PYTHON_BIN" -m pip install --upgrade pip

# 4️⃣ Install dependencies only if not installed
if [ ! -f "$VENV_DIR/installed.flag" ]; then
    echo "🟢 Installing Python dependencies..."
    "$PIP_BIN" install -r requirements.txt
    touch "$VENV_DIR/installed.flag"
else
    echo "🟢 Dependencies already installed."
fi

# 5️⃣ Debug info
echo "🟢 Using Python:"
"$PYTHON_BIN" -V
echo "🟢 Checking coinbase_advanced_py..."
"$PIP_BIN" show coinbase-advanced-py || echo "❌ coinbase_advanced_py not found!"

# 6️⃣ Run bot
echo "🚀 Starting Nija Trading Bot..."
exec "$PYTHON_BIN" nija_bot.py
