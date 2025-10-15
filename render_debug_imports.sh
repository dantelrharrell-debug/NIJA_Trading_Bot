# ====== Runtime import debug block - paste at top of nija_bot.py ======
import sys, os, traceback
print("=== RUNTIME DEBUG START ===")
print("sys.executable:", sys.executable)
print("sys.path:")
for p in sys.path:
    print("  ", p)

# Show installed distributions and top-level files for coinbase package
try:
    # Python 3.8+: importlib.metadata
    from importlib import metadata
    dists = list(metadata.distributions())
    print("Installed distributions (count):", len(dists))
    # Print names that look like 'coinbase' to narrow down
    cb_dists = [d for d in dists if 'coinbase' in (d.metadata.get('Name') or '').lower() or 'coinbase' in ' '.join(d.metadata.get_all('Top-Level', []) or [])]
    print("Distributions with 'coinbase' in name/top-level:", [ (d.metadata.get('Name'), d._path) for d in cb_dists ])
    # Also show top-level files from metadata (fallback)
    for d in cb_dists:
        try:
            print("---- dist:", d.metadata.get('Name'))
            files = list(d.files or [])[:200]
            print("    files sample:", files[:40])
        except Exception as e:
            print("    failed listing files:", e)
except Exception as e:
    print("importlib.metadata failed:", e)
    traceback.print_exc()

# Try direct pip-show style check
try:
    import subprocess
    py = sys.executable
    out = subprocess.check_output([py, "-m", "pip", "show", "coinbase-advanced-py"], text=True, stderr=subprocess.STDOUT)
    print("pip show coinbase-advanced-py:\n", out)
except Exception as e:
    print("pip show failed:", e)

# Attempt multiple import names and print results
import importlib
candidates = [
    "coinbase_advanced_py",
    "coinbase_advanced",
    "coinbase",
    "coinbase_advanced_py.client",
    "coinbase.client",
    "coinbase_advanced",
]
for name in candidates:
    try:
        m = importlib.import_module(name)
        loc = getattr(m, "__file__", repr(m))
        print(f"IMPORT OK -> {name}: {loc}")
        # print a short dir to see what it exposes
        print("  dir sample:", [x for x in dir(m) if not x.startswith("_")][:40])
    except Exception as e:
        print(f"IMPORT FAIL -> {name}: {e}")
        # print traceback for the first few failures
        traceback.print_exc(limit=1)

print("=== RUNTIME DEBUG END ===")
# ====== end debug block ======

#!/usr/bin/env bash
set -e
echo "=== render_debug_imports.sh ==="

# ensure venv
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt

PY="/opt/render/project/src/.venv/bin/python"
echo "Using python: $PY"

# list site-packages
$PY - <<'PYCODE'
import site, os, sys
for p in site.getsitepackages():
    print("site-packages:", p)
    try:
        print("contents:", os.listdir(p)[:200])
    except Exception as e:
        print("list failed:", e)
import pkgutil
mods = [m.name for m in pkgutil.iter_modules()]
print("summary top modules (first 200):", mods[:200])
PYCODE

# Quick import tests for common names
$PY - <<'PYCODE'
import importlib, traceback, sys
names = ["coinbase_advanced_py","coinbase_advanced","coinbase","coinbase_advanced_py.client","coinbase.client"]
for n in names:
    try:
        m = importlib.import_module(n)
        print("IMPORT OK:", n, "->", getattr(m,'__file__',str(m)))
    except Exception as e:
        print("IMPORT FAIL:", n, "->", e)
        traceback.print_exc()
PYCODE

echo "=== debug script done ==="
