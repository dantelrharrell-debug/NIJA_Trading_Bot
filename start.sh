#!/bin/bash
set -e  # Exit immediately if a command fails
set -o pipefail

# =========================
# 1️⃣ Activate virtual environment
# =========================
if [ -d ".venv" ]; then
    echo "✅ Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️ .venv not found, creating..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# =========================
# 2️⃣ Upgrade pip & install requirements
# =========================
echo "✅ Installing/upgrading pip and dependencies..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# =========================
# 3️⃣ Ensure vendor folder exists
# =========================
VENDOR_DIR="./vendor"
if [ ! -d "$VENDOR_DIR/coinbase_advanced_py" ]; then
    echo "❌ Vendor folder missing: $VENDOR_DIR/coinbase_advanced_py"
    echo "Please copy coinbase_advanced_py into the vendor folder."
    exit 1
else
    echo "✅ Vendor folder found: $VENDOR_DIR"
fi

# =========================
# 4️⃣ Start Nija Bot
# =========================
echo "🚀 Starting Nija Trading Bot..."
python3 nija_bot.py
