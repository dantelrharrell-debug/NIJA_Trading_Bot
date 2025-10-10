#!/usr/bin/env python3
import sys, os
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
VENDOR_DIR = str(ROOT / "vendor")

if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)
    print("✅ Added vendor to sys.path:", VENDOR_DIR)

try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except ModuleNotFoundError:
    print("❌ Module coinbase_advanced_py not found in vendor or site-packages")
    raise SystemExit(1)

# rest of your bot...
