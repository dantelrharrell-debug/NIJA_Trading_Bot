#!/usr/bin/env bash
set -eo pipefail

VENV=".venv"
PY="$VENV/bin/python3"

# Create virtual environment if missing
if [ ! -d "$VENV" ]; then
    echo "🟢 Creating virtual environment..."
    python3 -m venv "$VENV"
fi

# Upgrade pip in venv
echo "🔄 Upgrading pip..."
"$PY" -m pip install --upgrade pip

# Install dependencies in venv
echo "📦 Installing requirements..."
"$PY" -m pip install -r requirements.txt

# Install Coinbase package explicitly in venv
echo "🔍 Ensuring coinbase-advanced-py is installed..."
"$PY" -m pip install --no-cache-dir coinbase-advanced-py==1.8.2

# ✅ Run your bot using venv python
echo "🚀 Starting nija_bot.py..."
exec "$PY" nija_bot.py
