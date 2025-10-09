#!/bin/bash
set -e  # Exit immediately if a command fails

echo "🟢 Activating Python environment..."
# Render automatically uses the correct Python version; no need to manually activate

echo "🚀 Starting Nija Trading Bot..."
python3 nija_bot.py
