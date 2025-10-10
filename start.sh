#!/usr/bin/env bash
set -euo pipefail

# Print environment for debugging
echo "=== START.SH START ==="
echo "PWD: $(pwd)"
echo "Python: $(python3 --version 2>/dev/null || true)"
echo "PIP: $(python3 -m pip --version 2>/dev/null || true)"
echo "=== installing requirements ==="

# Always upgrade pip / setuptools first (Render may provide a venv automatically)
python3 -m pip install --upgrade pip setuptools wheel

# Install requirements into the environment Render provides
python3 -m pip install -r requirements.txt

echo "=== requirements installed ==="
echo "Files in repo root:"
ls -la | sed -n '1,200p'
echo "=== Running nija_bot.py ==="

# Exec your bot (so signals are passed properly)
exec python3 nija_bot.py
