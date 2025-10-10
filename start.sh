#!/bin/bash
set -euo pipefail

echo "🚀 Upgrading pip & installing requirements..."
python3 -m pip install --upgrade pip setuptools wheel --break-system-packages
python3 -m pip install --break-system-packages -r requirements.txt

echo "✅ Dependencies installed. Launching Nija Bot..."
exec python3 nija_bot.py
