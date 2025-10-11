#!/usr/bin/env bash
set -euo pipefail
echo "🚀 start.sh starting..."

# Make sure we use the venv python
if [ -x "./.venv/bin/python" ]; then
  echo "Using .venv python"
  exec ./.venv/bin/python nija_bot.py
else
  echo "No .venv found; falling back to system python"
  exec python3 nija_bot.py
fi
