#!/bin/bash
set -euo pipefail

echo "🟢 Ensuring virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

VENV_PY=".venv/bin/python"
VENV_PIP=".venv/bin/pip"

echo "🟢 Upgrading pip and installing dependencies..."
$VENV_PY -m pip install --upgrade pip
$VENV_PIP install -r requirements.txt

echo "🟢 Diagnostic info..."
echo "Python: $($VENV_PY -V)"
echo "Pip: $($VENV_PIP -V)"
$VENV_PY -m pip show coinbase-advanced-py || true

echo "🟢 Writing Coinbase PEM (from env)..."
if [ -n "${COINBASE_PEM:-}" ]; then
    echo "$COINBASE_PEM" > /tmp/my_coinbase_key.pem
    echo "✅ PEM written to /tmp/my_coinbase_key.pem"
else
    echo "⚠️ COINBASE_PEM not set, will use mock balances"
fi

echo "🟢 Starting Nija Trading Bot..."
$VENV_PY nija_bot.py
