#!/bin/bash
set -euo pipefail

echo "🚀 Render start.sh: upgrade pip & install requirements"

# Use the same python that Render will use
python3 -m pip install --upgrade pip setuptools wheel --break-system-packages

# Install requirements (Render usually does this in build, but ensure same env)
python3 -m pip install --break-system-packages -r requirements.txt

echo "✅ Dependencies installed. Running diagnostic & starting nija_bot.py..."
exec python3 nija_bot.py
