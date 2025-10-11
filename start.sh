#!/bin/bash
set -e

# ensure we use venv python (don't rely on Render activating things implicitly)
if [ ! -d ".venv" ]; then
  echo "❌ .venv missing; run build first"
  exit 1
fi

# Print which python and packages to help debugging
echo "Using python: $(./.venv/bin/python -V)"
echo "Which python: $(./.venv/bin/python -c 'import sys; print(sys.executable)')"

# Run bot using venv python
exec ./.venv/bin/python nija_bot.py
