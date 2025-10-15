#!/bin/bash
# Only create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Ensure latest pip & install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run the bot
python3 nija_bot.py

#!/bin/bash
# Activate venv if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Run the bot
python3 nija_bot.py

#!/usr/bin/env bash
# ---------------------------
# Nija Bot start script
# ---------------------------

echo "🚀 Starting Nija Bot..."

# ---------------------------
# Debug: check Coinbase modules
# ---------------------------
python3 - <<'END'
import importlib, pkgutil, json

names = ['coinbase_advanced_py','coinbase_advanced','coinbase','coinbase_advanced_py_client']
found = [{'name': n, 'spec': bool(importlib.util.find_spec(n))} for n in names]
print("🔎 Coinbase import candidates:")
print(json.dumps(found, indent=2))

print('--- installed top-level modules containing "coinbase" ---')
print('\n'.join([m.name for m in pkgutil.iter_modules() if 'coinbase' in m.name.lower()]))
END

# ---------------------------
# Run the Nija bot
# ---------------------------
# Make sure your bot's main file is named 'nija_bot.py' or update below
python3 nija_bot.py
