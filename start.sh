#!/usr/bin/env bash
# ------------------------------
# start.sh for Render deploy
# Handles venv, dependencies, and runs nija_bot.py
# ------------------------------

set -eo pipefail

VENV=".venv"
PY="$VENV/bin/python3"

echo "==> Setting up Python virtual environment..."

# 1️⃣ Create venv if missing
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi

# 2️⃣ Activate venv
source "$VENV/bin/activate"

# 3️⃣ Upgrade pip
pip install --upgrade pip

# 4️⃣ Install dependencies
pip install --no-cache-dir -r requirements.txt

# 5️⃣ Debug info (optional, remove in production)
echo "📦 Installed packages (head of pip freeze):"
pip freeze | head -n 20

echo "🚀 Starting nija_bot.py..."
python3 nija_bot.py
