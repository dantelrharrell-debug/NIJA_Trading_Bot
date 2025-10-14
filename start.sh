#!/bin/bash
# -------------------------------
# start.sh for Nija Bot on Render
# -------------------------------

# Exit on any error
set -e

# Absolute path to virtualenv Python
VENV_PYTHON="./.venv/bin/python"

# Check venv Python exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Virtual environment Python not found at $VENV_PYTHON"
    exit 1
fi

# Optional: upgrade pip in venv
$VENV_PYTHON -m pip install --upgrade pip

# Ensure Coinbase package is installed in venv
$VENV_PYTHON -m pip install --no-cache-dir coinbase-advanced-py==1.8.2

# Run your bot using venv Python directly
echo "🚀 Launching Nija bot..."
$VENV_PYTHON nija_bot.py
