#!/usr/bin/env bash
set -euo pipefail

# Activate venv
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

# Prefer dashboard env var; if not set, explicitly default to False
: "${USE_MOCK:=False}"
export USE_MOCK

echo "🔹 Python executable: $(which python3)"
echo "🔹 Starting NIJA Bot (USE_MOCK=${USE_MOCK})"
exec python3 nija_bot.py
