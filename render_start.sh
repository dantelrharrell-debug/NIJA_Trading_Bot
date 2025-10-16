#!/usr/bin/env bash
set -euo pipefail
echo "=== render_start.sh: begin ==="

echo "1) Show runtime python info"
. .venv/bin/activate
python --version
which python
echo "sys.executable reported above."

echo "2) Force-reinstall coinbase package into venv (ensure it's in runtime site-packages)"
pip install --upgrade pip
pip install --upgrade --force-reinstall coinbase-advanced-py==1.8.2

echo "3) List site-packages entries that look like coinbase* (for debugging):"
ls -la .venv/lib/python3.11/site-packages | egrep -i "coinbase|coin_base|coin|advanced" || true

echo "4) Try importing common module names and print results (will show import error if any):"
python - <<'PY'
import sys, pkgutil, traceback
print("Python executable:", sys.executable)
print("sys.path (head):", sys.path[:3])
candidates = [
    "coinbase_advanced_py",
    "coinbase_advanced",
    "coinbase",
    "coinbase_advancedpy",
    "coinbaseadvancedpy"
]
found = []
for name in candidates:
    try:
        m = __import__(name)
        print(f"IMPORT SUCCESS: {name} ->", getattr(m, "__file__", getattr(m, "__path__", "<built-in/module>")))
        found.append(name)
    except Exception as e:
        print(f"IMPORT FAIL: {name}: {e.__class__.__name__}: {e}")
print("pkgutil.iter_modules() top-level modules containing 'coinbase' or 'advanced':")
for p in pkgutil.iter_modules():
    if "coin" in p.name.lower() or "advanced" in p.name.lower():
        print(" -", p.name)
print("END import-check")
PY

echo "5) If import succeeded above, great. If not, print pip show info:"
pip show coinbase-advanced-py || true

echo "6) FINAL: start gunicorn with absolute venv binary"
exec .venv/bin/gunicorn -b 0.0.0.0:$PORT nija_bot:app
