#!/bin/bash
set -e
set -o pipefail

echo "🚀 Starting Nija Trading Bot..."

# -----------------------------
# 1️⃣ Activate virtual environment or create one
# -----------------------------
if [ -f ".venv/bin/activate" ]; then
    echo "🔹 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️ No .venv found, creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# -----------------------------
# 2️⃣ Upgrade pip and install dependencies
# -----------------------------
echo "🔹 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# -----------------------------
# 3️⃣ Ensure vendor folder exists for coinbase_advanced_py
# -----------------------------
if [ ! -d "vendor/coinbase_advanced_py" ]; then
    echo "⚠️ Vendor folder for coinbase_advanced_py not found!"
    mkdir -p vendor
    echo "🔹 Downloading coinbase_advanced_py..."
    python3 -m pip download coinbase-advanced-py==1.8.2 --no-deps -d ./vendor
    echo "🔹 Extracting..."
    for whl in ./vendor/coinbase-advanced-py-*.whl; do
        unzip -q "$whl" -d ./vendor/coinbase_advanced_py
    done
fi

# -----------------------------
# 4️⃣ Run the bot
# -----------------------------
echo "🔹 Running nija_bot.py..."
python3 nija_bot.py
