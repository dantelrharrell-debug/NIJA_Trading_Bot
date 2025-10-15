#!/bin/bash
# start.sh

# ----------------------
# 1. Activate virtual environment
# ----------------------
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    python3 -m venv .venv
    source .venv/bin/activate
fi

# ----------------------
# 2. Upgrade pip & install dependencies
# ----------------------
pip install --upgrade pip
pip install -r requirements.txt

# ----------------------
# 3. Debug info (optional)
# ----------------------
echo "🟢 Python executable being used: $(which python)"
echo "🟢 Pip executable being used: $(which pip)"
python -m pip show coinbase-advanced-py

# ----------------------
# 4. Run the bot
# ----------------------
python nija_bot.py
