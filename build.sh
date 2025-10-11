#!/usr/bin/env bash
set -euo pipefail
echo "🛠️  build.sh starting..."

# 1) Create .venv if missing
if [ ! -d ".venv" ]; then
  echo "Creating virtualenv .venv..."
  python3 -m venv .venv
fi

# 2) Use venv's python to upgrade pip and install deps
echo "Using venv python: ./.venv/bin/python"
./.venv/bin/python -m pip install --upgrade pip setuptools wheel

# 3) Install requirements into the venv
./.venv/bin/python -m pip install -r requirements.txt

# 4) Ensure coinbase lib exists (explicit)
./.venv/bin/python -m pip install coinbase-advanced-py==1.8.2

# 5) quick import check (fails build if import broken)
./.venv/bin/python -c "import coinbase_advanced_py; print('✅ coinbase_advanced_py import ok')"

echo "🛠️  build.sh finished"
