#!/bin/bash
# -------------------------------
# start.sh for Nija bot on Render
# -------------------------------

# 1️⃣ Activate virtual environment
if [ -f .venv/bin/activate ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "❌ Virtual environment not found, creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# 2️⃣ Upgrade pip inside venv
python -m pip install --upgrade pip

# 3️⃣ Reinstall dependencies to ensure venv has them
echo "Installing required packages..."
python -m pip install --no-cache-dir -r requirements.txt

# 4️⃣ Launch Nija bot
echo "🚀 Launching Nija bot..."
python nija_bot.py
