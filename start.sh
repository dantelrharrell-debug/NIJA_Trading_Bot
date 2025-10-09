#!/bin/bash
set -e  # Exit immediately if a command fails
set -o pipefail

echo "🚀 Starting Nija Trading Bot..."

# -----------------------------
# 1️⃣ Activate virtual environment if it exists
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
# 3️⃣ Ensure vendor folder exists
# -----------------------------
if [ ! -d "vendor/coinbase_advanced_py" ]; then
    echo "⚠️ Vendor folder for coinbase_advanced_py not found!"
    echo "🔹 Downloading and vendoring coinbase_advanced_py..."
    mkdir -p vendor
    python3 -m pip download coinbase-advanced-py==1.8.2 --no-deps -d ./vendor
    unzip ./vendor/coinbase-advanced-py-1.8.2-py3-none-any.whl -d ./vendor/coinbase_advanced_py
fi

# -----------------------------
# 4️⃣ Run the bot
# -----------------------------
echo "🔹 Running nija_bot.py..."
python3 nija_bot.py
