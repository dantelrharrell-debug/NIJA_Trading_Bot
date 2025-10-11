#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Creating local venv..."
python3 -m venv .venv

echo "🔹 Activating venv and installing dependencies..."
. .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install --force-reinstall coinbase-advanced-py==1.8.2

if [ -f requirements.txt ]; then
    python -m pip install -r requirements.txt
fi

echo "✅ Build complete. venv ready at .venv/"
