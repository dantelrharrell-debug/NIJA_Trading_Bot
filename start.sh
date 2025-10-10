#!/bin/bash
set -euo pipefail

echo "🚀 Render start.sh: upgrading pip & installing requirements"

# Upgrade pip, setuptools, wheel inside Render's environment
python3 -m pip install --upgrade pip setuptools wheel --break-system-packages

# Install requirements inside Render's venv
python3 -m pip install --break-system-packages -r requirements.txt

echo "✅ Dependencies installed. Launching bot..."
exec python3 nija_bot.py
