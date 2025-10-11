#!/bin/bash

# Upgrade pip and install dependencies first
python3 -m pip install --upgrade pip
python3 -m pip install --no-cache-dir -r requirements.txt

# Now run your bot
python3 nija_bot.py#!/bin/bash
set -euo pipefail

echo "🚀 Render start.sh: upgrade pip & install requirements"

# Use same interpreter that Render provides
python3 -m pip install --upgrade pip setuptools wheel --break-system-packages
python3 -m pip install --break-system-packages -r requirements.txt

echo "✅ Dependencies installed. Launching bot..."
exec python3 nija_bot.py
