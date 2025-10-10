#!/usr/bin/env python3
import sys
from pathlib import Path

# Add vendor folder to sys.path
ROOT = Path(__file__).parent.resolve()
VENDOR_DIR = str(ROOT / "vendor")
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)
    print("✅ Added vendor to sys.path:", VENDOR_DIR)

# Now import coinbase_advanced_py
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except ModuleNotFoundError:
    print("❌ Module coinbase_advanced_py not found in vendor or site-packages")
    raise SystemExit(1)

# Continue with your bot logic...
