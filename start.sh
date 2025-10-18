#!/usr/bin/env bash
set -euo pipefail
echo "=== START: container entrypoint ==="
python --version || true
pip --version || true
echo "Starting NIJA bot..."
exec python nija_bot.py
