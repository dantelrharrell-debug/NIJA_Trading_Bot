#!/bin/bash

# ---------- START.RS: Safe Nija Bot Launcher for Render ----------

# Exit on any errors
set -e

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🛠 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate the virtual environment
echo "⚡ Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install required packages from requirements.txt
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Confirm coinbase_advanced_py is installed
python3 - <<'EOF'
import sys
import importlib.util
spec = importlib.util.find_spec("coinbase_advanced_py")
if spec is None:
    print("❌ coinbase_advanced_py NOT found!")
else:
    print("✅ coinbase_advanced_py found!")
EOF

# Start the bot
echo "🚀 Launching Nija bot..."
exec python3 nija_bot.py
