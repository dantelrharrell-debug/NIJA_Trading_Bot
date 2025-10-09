#!/bin/bash
set -euo pipefail

echo "🚀 start.sh — booting Nija Trading Bot"

# 1) Create venv if missing
if [ ! -d ".venv" ]; then
  echo "🛠 .venv not found — creating virtual environment..."
  python3 -m venv .venv
fi

# 2) Use the venv python directly to avoid shell activation oddness
VENV_PY="./.venv/bin/python3"
VENV_PIP="./.venv/bin/pip"

# 3) Upgrade pip (Render uses externally-managed Python so we allow break)
echo "📦 Upgrading pip inside venv..."
$VENV_PIP install --upgrade pip --break-system-packages

# 4) Install requirements into venv
if [ -f "requirements.txt" ]; then
  echo "📥 Installing requirements from requirements.txt..."
  $VENV_PIP install --break-system-packages -r requirements.txt
else
  echo "⚠️ requirements.txt not found in repo root — continuing without it."
fi

# 5) Ensure coinbase package definitely installed (explicit install)
echo "🔎 Ensuring coinbase-advanced-py is installed in venv..."
$VENV_PIP install --break-system-packages coinbase-advanced-py==1.8.2 || true

# 6) Verify package importability (fail early with useful debug)
echo "🔁 Verifying coinbase_advanced_py import..."
$VENV_PY - <<'PYTEST'
try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py import OK — version:", getattr(cb, "__version__", "unknown"))
except Exception as e:
    import sys, traceback
    print("❌ coinbase_advanced_py import FAILED:", file=sys.stderr)
    traceback.print_exc()
    sys.exit(2)
PYTEST

# 7) Print helpful env info
echo "📋 Environment variables (sensitive values omitted):"
echo "  SANDBOX=${SANDBOX:-<not-set>}"
echo "  TRADE_SYMBOLS=${TRADE_SYMBOLS:-<not-set>}"
echo "  PORT=${PORT:-<not-set>}"

# 8) Run the bot using the venv python (unbuffered stdout)
echo "🏁 Running nija_bot.py with venv python..."
exec $VENV_PY -u nija_bot.py
