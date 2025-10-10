#!/bin/bash
set -euo pipefail

echo "🚀 Render start.sh: upgrade pip & install requirements"

python3 -m pip install --upgrade pip setuptools wheel --break-system-packages
# Install requirements (if any). If you vendor coinbase, you can keep or remove coinbase-advanced-py from requirements.txt
python3 -m pip install --break-system-packages -r requirements.txt

echo "✅ Dependencies installed. Launching bot..."
exec python3 nija_bot.py
