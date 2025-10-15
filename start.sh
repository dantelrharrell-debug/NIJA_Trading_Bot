#!/bin/bash
set -euo pipefail

echo "🟢 Activating venv..."
source .venv/bin/activate

echo "🟢 Installing dependencies (safe - pip will skip already satisfied)..."
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "🚀 Starting Nija Bot..."
python nija_bot.py
