#!/bin/bash
set -e

# -----------------------------
# 1️⃣ Activate virtual environment
# -----------------------------
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Activated virtual environment"
else
    echo "❌ .venv not found — make sure you installed dependencies"
    exit 1
fi

# -----------------------------
# 2️⃣ Ensure vendor folder exists
# -----------------------------
VENDOR_DIR="./vendor"
if [ ! -d "$VENDOR_DIR/coinbase_advanced_py" ]; then
    echo "❌ Vendor folder or coinbase_advanced_py missing"
    exit 1
fi
echo "✅ Vendor folder verified"

# -----------------------------
# 3️⃣ Export environment variables (replace with your real keys on Render dashboard)
# -----------------------------
export API_KEY="${API_KEY:-fake_key}"
export API_SECRET="${API_SECRET:-fake_secret}"
export DRY_RUN="${DRY_RUN:-True}"

# -----------------------------
# 4️⃣ Run the bot
# -----------------------------
echo "🚀 Starting Nija Trading Bot..."
python3 nija_bot.py
