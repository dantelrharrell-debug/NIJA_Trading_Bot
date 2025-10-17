#!/usr/bin/env bash
set -euo pipefail
echo "---- START.SH: runtime diagnostics ----"
python -V
pip -V

echo "---- Ensure requirements installed (redundant but safe) ----"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

echo "---- PIP SHOW / LIST FOR coinbase ----"
python - <<'PY'
import sys, pkgutil, importlib, os, site, traceback
import pkg_resources

print("sys.executable:", sys.executable)
print("sys.path (filtered):")
for p in sys.path:
    if p and ('site-packages' in p or 'dist-packages' in p):
        print("  ", p)

print("\nPIP packages with 'coinbase' in key:")
for d in pkg_resources.working_set:
    if 'coinbase' in d.key.lower():
        print("  ->", d.key, d.version, "installed at", getattr(d, 'location', None))

# list matching files in site-packages
sitepkgs = [p for p in sys.path if p and ('site-packages' in p or 'dist-packages' in p)]
found = []
for sp in sitepkgs:
    try:
        for name in os.listdir(sp):
            if name.lower().startswith('coinbase'):
                found.append((sp, name))
    except Exception:
        pass

print("\nsite-packages coinbase* entries (first 100):")
for sp,name in found[:100]:
    print("  ", sp, "/", name)

print("\nTry importing known variations:")
candidates = ['coinbase_advanced_py', 'coinbase_advanced', 'coinbase_advanced_api', 'coinbase_advanced_py-1.8.2', 'coinbase']
for cand in candidates:
    try:
        m = importlib.import_module(cand)
        print(f"IMPORT OK: {cand} ->", getattr(m, '__file__', getattr(m, '__path__', 'package-no-file')))
    except Exception as e:
        print(f"IMPORT FAIL: {cand} -> {type(e).__name__}: {e}")

# If none imported, print a sample of files inside the first site-packages
if not found:
    sample = []
    for sp in sitepkgs:
        try:
            sample += os.listdir(sp)
        except Exception:
            pass
    print("\nNo coinbase* found. site-packages sample (first 50):")
    print(sample[:50])
    # helpful hint exit code for Railway logs visibility
    sys.exit(2)

print("\nDiagnostics done.")
PY

echo "---- If diagnostics passed, running trading_worker_live.py ----"
python trading_worker_live.py
