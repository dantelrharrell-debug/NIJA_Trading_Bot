#!/usr/bin/env bash
set -e  # Exit immediately if a command fails
set -o pipefail  # Fail on errors in piped commands

# -----------------------------
# 1️⃣ Activate virtual environment
# -----------------------------
if [ -d ".venv" ]; then
    echo "✅ Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️ .venv not found, creating..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# -----------------------------
# 2️⃣ Upgrade pip and install requirements
# -----------------------------
echo "🔧 Installing dependencies..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# -----------------------------
# 3️⃣ Ensure vendor folder is present
# -----------------------------
if [ ! -d "vendor/coinbase_advanced_py" ]; then
    echo "❌ vendor/coinbase_advanced_py not found. Make sure you added it to your repo."
    exit 1
fi

# -----------------------------
# 4️⃣ Export environment variables (optional)
# -----------------------------
# If you are storing secrets in Render dashboard, skip this
# export API_KEY="your_api_key_here"
# export API_SECRET="your_api_secret_here"

# -----------------------------
# 5️⃣ Start the bot
# -----------------------------
echo "🚀 Starting Nija Trading Bot..."
python3 nija_bot.py
