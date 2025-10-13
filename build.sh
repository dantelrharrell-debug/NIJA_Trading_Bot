#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting build..."

# 1. Create or reuse virtualenv
python3 -m venv .venv

# 2. Ensure pip present in venv and upgrade tools
.venv/bin/python -m ensurepip --upgrade
.venv/bin/pip install --upgrade pip setuptools wheel

# 3. Install requirements into the venv
.venv/bin/pip install -r requirements.txt

echo "✅ Requirements installed"

# 4. Debug: verify venv python & coinbase availability
.venv/bin/python - <<'PY'
import sys, pkgutil
print("VENV PYTHON:", sys.executable)
print("sys.path (first 6):", sys.path[:6])
print("coinbase_advanced_py loader:", pkgutil.find_loader("coinbase_advanced_py"))
PY

# 5. Run the app with the venv python
.venv/bin/python main.py
echo "🚀 Bot started"
