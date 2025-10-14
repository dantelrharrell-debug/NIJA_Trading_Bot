#!/bin/bash
# start.sh for Nija Bot on Render

set -e

# Use the venv Python directly
VENV_PY="./.venv/bin/python"

# Ensure the venv Python exists
if [ ! -f "$VENV_PY" ]; then
    echo "❌ Virtualenv Python not found!"
    exit 1
fi

# Run the bot using the venv Python
echo "🚀 Launching Nija bot..."
$VENV_PY nija_bot.py
