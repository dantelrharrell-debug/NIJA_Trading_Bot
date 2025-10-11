#!/usr/bin/env bash
set -euo pipefail

echo "🚀 start.sh starting..."

# Use the venv python directly to avoid shell `source` differences
VENV_PY="./.venv/bin/python"
echo "Using python: $($VENV_PY -V)"

# Optional: print which packages are available (debug)
$VENV_PY -c "import sys, pkgutil; print('sys.executable=', sys.executable); print('coinbase package found=', pkgutil.find_loader('coinbase') is not None)"

# Run your bot
$VENV_PY nija_bot.py
