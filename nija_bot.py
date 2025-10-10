import pkgutil, importlib, sys

print("site-packages scan (prefix):", sys.path[:4])
for m in pkgutil.iter_modules():
    name = m.name
    if name.startswith("coinbase"):
        print("found coinbase-ish module:", name)

import os
from dotenv import load_dotenv
# (then your existing code below)
#!/usr/bin/env python3
import sys, os
from pathlib import Path
ROOT = Path(__file__).parent.resolve()
VENDOR_DIR = str(ROOT / "vendor")
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)
    print("✅ Added vendor to sys.path:", VENDOR_DIR)
print("sys.path head:", sys.path[:4])

# Try both possible names (some installs expose top-level 'coinbase' vs 'coinbase_advanced_py')
cb = None
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except Exception as e:
    print("ℹ️ coinbase_advanced_py import failed:", type(e).__name__, e)
    try:
        import coinbase as cb
        print("✅ Imported coinbase (fallback):", getattr(cb, "__version__", "unknown"))
    except Exception as e2:
        print("❌ coinbase import also failed:", type(e2).__name__, e2)
        raise SystemExit(1)

# Minimal sanity test - try to discover a client or helper
client = None
if hasattr(cb, "Client"):
    try:
        client = cb.Client("fake", "fake")
        print("✅ Created client instance via cb.Client (test)")
    except Exception as e:
        print("ℹ️ cb.Client exists but instantiation failed (expected with fake keys):", e)
else:
    print("ℹ️ cb.Client attribute not found, examine cb module:", dir(cb)[:50])

print("🚀 nija_bot import check complete")
