#!/usr/bin/env bash
set -euo pipefail

echo "=== START: container entrypoint ==="
python --version || true
pip --version || true

# Ensure env sanity (optional debug)
echo "PORT=${PORT:-10000}"
echo "Starting NIJA bot..."
exec python nija_bot.py
