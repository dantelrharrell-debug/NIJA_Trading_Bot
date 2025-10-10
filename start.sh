#!/bin/bash
set -euo pipefail

echo "🚀 Render start.sh: upgrade pip & install requirements"

# Upgrade pip and install requirements in the Render Python env
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -r requirements.txt

echo "✅ Dependencies installed. Launching Nija Bot..."
python3 nija_bot.py
