#!/usr/bin/env bash
set -euo pipefail

echo "🔹 DEBUG START.SH — start"
echo "pwd: $(pwd)"
echo "ls -la:"
ls -la

# Activate venv if it exists
if [ -f .venv/bin/activate ]; then
  echo "🔹 Activating .venv"
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  echo "❗ .venv not found at .venv/bin/activate"
fi

echo "Python executable: $(which python3 || true)"
python3 --version || true

# Show first 30 installed packages (mask long list)
echo "pip list (head 30):"
pip3 list --format=columns | head -n 30 || true

# Print key env items (mask secrets)
echo "ENV: USE_MOCK='${USE_MOCK-<not set>}'"
echo "ENV: API_KEY='${API_KEY-<not set>}'"   # this will print literal value if set — remove if you don't want it visible
if [ -n "${API_SECRET-}" ]; then
  echo "ENV: API_SECRET is set (masked)"
else
  echo "ENV: API_SECRET not set"
fi

echo "🔹 Running nija_bot.py now..."
exec python3 nija_bot.py
