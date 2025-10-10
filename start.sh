#!/bin/bash
set -euo pipefail

echo "⛏️ Build & start (start.sh) — $(date)"
echo "Python executable: $(which python3)  ($(python3 --version))"

# Install packages into the same python used to run the bot.
python3 -m pip install --upgrade pip setuptools wheel --break-system-packages
python3 -m pip install --break-system-packages -r requirements.txt

echo "✅ Packages installed. Launching bot..."
exec python3 nija_bot.py
