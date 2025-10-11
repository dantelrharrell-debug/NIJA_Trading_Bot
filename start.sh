#!/usr/bin/env bash
set -euo pipefail

# Activate local venv
if [ -d .venv ]; then
  . .venv/bin/activate
else
  echo "❌ .venv not found. Run build first."
  exit 1
fi

echo "🚀 Starting nija bot..."
exec python nija_bot.py
