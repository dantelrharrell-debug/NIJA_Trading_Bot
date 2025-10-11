#!/usr/bin/env bash
set -euo pipefail
echo "🛠️  build.sh starting..."

# remove stale venv to avoid weird state
rm -rf .venv

# create venv
python3 -m venv .venv

# always use venv python when installing
./.venv/bin/python -m pip install --upgrade pip setuptools wheel

# install everything from requirements.txt (includes coinbase)
./.venv/bin/python -m pip install -r requirements.txt

# fallback explicit install (harmless if already installed)
./.venv/bin/python -m pip install coinbase-advanced-py==1.8.2

# quick runtime import check inside venv
./.venv/bin/python -c "import coinbase_advanced_py; print('✅ coinbase_advanced_py import ok')"

echo "🛠️  build.sh finished"
