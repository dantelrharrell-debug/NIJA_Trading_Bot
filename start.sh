#!/bin/bash
set -euo pipefail

echo "⛏️  Build & start (start.sh) — $(date)"
echo "Python executable: $(which python3)  ($(python3 --version))"

# Upgrade pip/tools in the Render environment then install requirements.
# Use --break-system-packages because Render uses an "externally managed" env.
python3 -m pip install --upgrade pip setuptools wheel --break-system-packages
python3 -m pip install --break-system-packages -r requirements.txt

echo "✅ Packages installed. Launching bot..."
exec python3 nija_bot.py
