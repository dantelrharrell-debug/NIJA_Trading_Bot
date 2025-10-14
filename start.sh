#!/usr/bin/env bash
set -eo pipefail

# ------------------------------
# start.sh - Render deploy starter
# ------------------------------

VENV=".venv"
PY="$VENV/bin/python3"

# 1️⃣ Create virtual environment if missing
if [ ! -d "$VENV" ]; then
    echo "🟢 Creating virtual environment..."
    python3 -m venv "$VENV"
fi

# 2️⃣ Activate virtual environment
source "$VENV/bin/activate"

# 3️⃣ Upgrade pip
echo "🔄 Upgrading pip..."
pip install --upgrade pip

# 4️⃣ Install dependencies
echo "📦 Installing requirements..."
pip install -r requirements.txt

# 5️⃣ Ensure coinbase-advanced-py is importable
echo "🔍 Checking Coinbase library..."
if ! "$PY" -c "import coinbase_advanced_py" &> /dev/null; then
    echo "⚠️ coinbase_advanced_py not found, installing..."
    pip install --no-cache-dir coinbase-advanced-py==1.8.2
fi

# 6️⃣ Run the bot
echo "🚀 Starting nija_bot.py..."
exec "$PY" nija_bot.py
