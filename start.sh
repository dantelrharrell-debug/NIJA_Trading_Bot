#!/usr/bin/env bash
set -e

echo "🚀 Starting Nija Trading Bot..."

# 1️⃣ Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo "Activating .venv..."
    source .venv/bin/activate
else
    echo "❌ .venv not found. Creating..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# 2️⃣ Upgrade pip and install requirements
echo "Installing dependencies..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# 3️⃣ Add vendor folder to PYTHONPATH for coinbase_advanced_py
VENDOR_DIR="$(pwd)/vendor"
if [ -d "$VENDOR_DIR" ]; then
    export PYTHONPATH="$VENDOR_DIR:$PYTHONPATH"
    echo "✅ Vendor path added to PYTHONPATH: $VENDOR_DIR"
else
    echo "⚠️ Vendor folder not found: $VENDOR_DIR"
fi

# 4️⃣ Run bot
python3 nija_bot.py
