#!/bin/bash
# start.sh -- debug-first then run bot

set -euo pipefail

# 1) ensure venv
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

VENV_PY=".venv/bin/python"
VENV_PIP=".venv/bin/pip"

# 2) install deps (safe - pip will skip already satisfied)
$VENV_PY -m pip install --upgrade pip
$VENV_PIP install -r requirements.txt

# 3) basic debug info
echo "🟢 Using Python: $($VENV_PY -V)"
echo "🟢 Pip: $($VENV_PIP -V)"
echo "🟢 coinbase-advanced-py info (pip):"
$VENV_PY -m pip show coinbase-advanced-py || true

# 4) Diagnostic: list site-packages + try import candidates (THIS MUST RUN BEFORE BOT)
$VENV_PY - <<'PY'
import sys, os, pkgutil, importlib, importlib.metadata
print("----- PYTHON -----")
print(sys.executable)
print(sys.version)
# site-packages paths
sp = [p for p in sys.path if "site-packages" in p]
print("SITE-PACKAGES:", sp)
for p in sp:
    try:
        print("\n--- listing:", p)
        items = sorted([n for n in os.listdir(p) if "coinbase" in n.lower() or "coinbase_advanced" in n.lower()])
        for it in items[:200]:
            print("  ", it)
    except Exception as e:
        print("  (list error)", e)

# pkgutil scan
print("\n--- pkgutil scan for coinbase modules ---")
mods=[]
for p in sp:
    try:
        mods += [m.name for m in pkgutil.iter_modules([p]) if "coinbase" in m.name.lower()]
    except Exception:
        pass
print(sorted(set(mods)))

# metadata: distribution top-level packages (if available)
print("\n--- importlib.metadata top-level (distribution coinbase-advanced-py) ---")
try:
    dist = importlib.metadata.distribution("coinbase-advanced-py")
    top = dist.read_text("top_level.txt")
    print("top_level.txt:", repr(top))
except Exception as e:
    print("metadata error:", type(e).__name__, e)

# Try imports with common candidate names
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

# 5) If diagnostic passed, run the bot (non-exec so logs continue)
echo "🚀 Starting Nija Trading Bot..."
.venv/bin/python nija_bot.py
