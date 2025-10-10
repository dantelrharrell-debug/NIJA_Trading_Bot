#!/bin/bash
set -euo pipefail

echo "🚀 Render start.sh: upgrading pip & installing requirements"

# Use Python from Render venv
PYTHON_BIN=$(which python3)

# Upgrade pip, setuptools, wheel inside this Python environment
$PYTHON_BIN -m pip install --upgrade pip setuptools wheel --break-system-packages

# Install requirements using the same interpreter
$PYTHON_BIN -m pip install --break-system-packages -r requirements.txt

echo "✅ Dependencies installed. Launching bot..."

# Launch bot with same interpreter
exec $PYTHON_BIN nija_bot.py
