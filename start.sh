#!/usr/bin/env bash
set -euo pipefail

# Activate our venv and run the bot
if [ -d .venv ]; then
  . .venv/bin/activate
else
  echo "❗ .venv not found — run build first or check build logs"
  exit 1
fi

echo "🚀 Starting nija bot with .venv/python ..."
# Replace nija_bot.py with your entrypoint filename if different
exec python nija_bot.py
