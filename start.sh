#!/bin/bash
set -euo pipefail  # exit on error, treat unset vars as errors

echo "🟢 Activating venv..."
source .venv/bin/activate

VENV_PY=".venv/bin/python"
VENV_PIP=".venv/bin/pip"

# Ensure dependencies
$VENV_PY -m pip install --upgrade pip
$VENV_PIP install -r requirements.txt

# Debug info
echo "🟢 Using Python: $($VENV_PY -V)"
echo "🟢 Pip: $($VENV_PIP -V)"
$VENV_PY -m pip show coinbase-advanced-py || true

# Diagnostic: check packages and imports
$VENV_PY - <<'PY'
import sys, os, pkgutil, importlib, importlib.metadata
print("----- PYTHON -----")
print(sys.executable, sys.version)
sp = [p for p in sys.path if "site-packages" in p]
print("SITE-PACKAGES:", sp)
for p in sp:
    try:
        items = sorted([n for n in os.listdir(p) if "coinbase" in n.lower() or "coinbase_advanced" in n.lower()])
        for it in items[:200]:
            print("  ", it)
    except Exception as e:
        print("  (list error)", e)

print("\n--- pkgutil scan ---")
mods=[]
for p in sp:
    try:
        mods += [m.name for m in pkgutil.iter_modules([p]) if "coinbase" in m.name.lower()]
    except Exception:
        pass
print(sorted(set(mods)))

print("\n--- import attempts ---")
candidates = [
    "coinbase_advanced_py",
    "coinbase_advanced",
    "coinbase",
    "coinbase_advanced_py_client",
    "coinbase_advanced_py.api",
    "coinbase.advanced",
]
for name in candidates:
    try:
        importlib.import_module(name)
        print("IMPORT OK ->", name)
    except Exception as e:
        print("IMPORT FAIL ->", name, ":", type(e).__name__, e)
PY

# PEM setup for live trading (optional)
if [ -n "${COINBASE_PEM:-}" ]; then
    echo "$COINBASE_PEM" > /tmp/my_coinbase_key.pem
    echo "✅ PEM written to /tmp/my_coinbase_key.pem"
fi

# Run bot
echo "🚀 Starting Nija Bot..."
$VENV_PY nija_bot.py
