#!/usr/bin/env bash
set -euo pipefail
echo "🚀 start.sh starting..."

if [ ! -d ".venv" ]; then
  echo "❗ .venv missing — did the build step run?"
  exit 1
fi

# verify package is available in the venv runtime
./.venv/bin/python -c "import coinbase_advanced_py; print('✅ coinbase_advanced_py available in runtime')"

# run the bot using the venv python
exec ./.venv/bin/python nija_bot.py
