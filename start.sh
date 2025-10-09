#!/bin/bash
set -e
set -o pipefail

# Activate virtualenv
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Upgrade pip & install requirements
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

# Setup vendor modules automatically
python3 setup_vendor.py

# Start the bot
python3 nija_bot.py
