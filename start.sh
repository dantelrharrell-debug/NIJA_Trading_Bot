#!/usr/bin/env bash
set -e

echo "🔧 Ensuring coinbase-advanced-py is installed..."
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir coinbase-advanced-py==1.8.2

echo "🚀 Launching NIJA Bot..."
python3 nija_bot.py

#!/usr/bin/env bash
set -e

echo "🔧 Activating virtualenv and reinstalling coinbase-advanced-py..."
source .venv/bin/activate

pip uninstall -y coinbase-advanced-py
pip install --no-cache-dir coinbase-advanced-py==1.8.2

echo "✅ Dependencies ready. Build complete."
