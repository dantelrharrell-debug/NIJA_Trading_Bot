#!/bin/bash
# start.sh — optimized, pre-built wheels for fast deploy

# ----------------------
# 1️⃣ Activate or create virtual environment
# ----------------------
if [ -d ".venv" ]; then
    echo "🟢 Activating existing virtual environment..."
else
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

# ----------------------
# 2️⃣ Install dependencies if missing (use wheels for heavy packages)
# ----------------------
REQUIRED_PKG="coinbase-advanced-py"
PKG_OK=$(.venv/bin/python -m pip show $REQUIRED_PKG | grep Version)

if [ -z "$PKG_OK" ]; then
    echo "📦 Installing dependencies..."
    .venv/bin/python -m pip install --upgrade pip wheel setuptools

    # Pre-install heavy packages from wheels to avoid long builds
    .venv/bin/python -m pip install numpy pandas cryptography

    # Install the rest of your requirements
    .venv/bin/python -m pip install -r requirements.txt --no-deps
else
    echo "✅ Dependencies already installed"
fi

# ----------------------
# 3️⃣ Debug info
# ----------------------
echo "🟢 Python executable: $(which python)"
.venv/bin/python -m pip show coinbase-advanced-py

# ----------------------
# 4️⃣ Run Nija bot explicitly using venv Python
# ----------------------
echo "🚀 Starting Nija Trading Bot..."
.venv/bin/python nija_bot.py
