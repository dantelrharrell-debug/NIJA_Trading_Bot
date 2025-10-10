#!/bin/bash
set -euo pipefail

PYTHON_BIN=$(which python3)
$PYTHON_BIN -m pip install --upgrade pip setuptools wheel --break-system-packages
$PYTHON_BIN -m pip install --break-system-packages -r requirements.txt

echo "✅ Dependencies installed. Launching bot..."
exec $PYTHON_BIN nija_bot.py
