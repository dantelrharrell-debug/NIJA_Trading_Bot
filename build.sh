#!/usr/bin/env bash
set -euo pipefail

echo "🛠️  build.sh starting..."

# 1) create venv (if not present)
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# 2) use the venv python directly
VENV_PY="./.venv/bin/python"

echo "Using python: $($VENV_PY -V)"

# 3) upgrade pip inside venv
$VENV_PY -m pip install --upgrade pip

# 4) install dependencies (requirements.txt) and explicit coinbase package
$VENV_PY -m pip install -r requirements.txt
$VENV_PY -m pip install coinbase-advanced-py==1.8.2

# sanity check: verify import inside venv
$VENV_PY -c "from coinbase.rest import RESTClient; print('✅ coinbase.rest import ok')"

echo "🛠️  build.sh finished"
