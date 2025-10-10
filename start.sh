#!/bin/bash
set -euo pipefail

echo "🚀 Render start.sh: upgrade pip & install requirements"

# Upgrade pip, setuptools, wheel
python3 -m pip install --upgrade pip setuptools wheel --break-system-packages

# Install dependencies
python3 -m pip install --break-system-packages -r requirements.txt

echo "✅ Dependencies installed. Launching Nija Bot..."
exec python3 nija_bot.py
