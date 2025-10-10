#!/usr/bin/env python3
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.resolve()

# Ensure vendor folder is first in sys.path so vendored packages are found
VENDOR_DIR = str(ROOT / "vendor")
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)
    print("✅ Added vendor to sys.path:", VENDOR_DIR)

# Optional: show a small sys.path head (helpful for debugging)
print("sys.path head:", sys.path[:4])

# Try to import the vendored package
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except ModuleNotFoundError as e:
    print("❌ Module coinbase_advanced_py not found in vendor or site-packages:", e)
    raise SystemExit(1)

# Load env (local dev .env will be loaded if present)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env (if present)")
except Exception:
    # python-dotenv may or may not be present on some systems — that's ok on Render if env vars are set there.
    pass

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() == "true"
SANDBOX = os.getenv("SANDBOX", "True").lower() == "true"

if not API_KEY or not API_SECRET:
    print("⚠️ Missing API_KEY or API_SECRET environment variables. Set them in Render (or create a .env locally).")
    if not DRY_RUN:
        raise SystemExit(1)

# Initialize client — package internals may differ; try common entrypoints
client = None
# 1) try direct Client class
if client is None:
    try:
        Client = getattr(cb, "Client", None)
        if Client:
            client = Client(API_KEY or "fake", API_SECRET or "fake")
            print("✅ Client created via cb.Client")
    except Exception as e:
        print("ℹ️ cb.Client failed:", type(e).__name__, e)

# 2) try top-level helper functions (older/newer variants)
if client is None:
    try:
        # Example: some packages expose functional entrypoints
        if hasattr(cb, "get_accounts"):
            client = cb  # wrapper-style
            print("✅ Using module-level functions on cb")
    except Exception:
        pass

if client is None:
    print("❌ Could not create a Coinbase client object from vendored package.")
    # show file listing for debugging
    try:
        print("vendor listing:", os.listdir(VENDOR_DIR)[:20])
    except Exception:
        pass
    raise SystemExit(1)

# Example usage: attempt to list balances (guarded)
try:
    if hasattr(client, "get_account_balances"):
        balances = client.get_account_balances()
        print("💰 Balances:", balances)
    elif hasattr(client, "get_accounts"):
        accounts = client.get_accounts()
        print("💰 Accounts:", accounts)
    else:
        print("ℹ️ Client has no known balance/account method. Explore client attributes:", dir(client)[:40])
except Exception as e:
    print("⚠️ Error calling client API:", type(e).__name__, e)

# Your trading logic continues here...
print("🚀 Nija Trading Bot initialized (DRY_RUN=%s SANDBOX=%s)" % (DRY_RUN, SANDBOX))
