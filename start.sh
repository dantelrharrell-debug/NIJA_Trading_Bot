#!/bin/bash
set -euo pipefail

echo "🚀 Render start.sh: upgrade pip & install requirements"

# Ensure pip installs inside the Render virtualenv
python3 -m pip install --upgrade pip setuptools wheel --break-system-packages
python3 -m pip install --break-system-packages -r requirements.txt

echo "✅ Dependencies installed. Launching Nija Bot..."

# Run Python using the virtualenv
exec python3 nija_bot.py
