#!/usr/bin/env python3
import os
import sys
import subprocess
import site
from pathlib import Path
import time

ROOT = Path(__file__).parent.resolve()
print("🚀 Starting Nija Trading Bot")
print("Python executable:", sys.executable)
print("Working dir:", ROOT)
print("sys.path head:", sys.path[:6])
print("site.getsitepackages():", getattr(site, "getsitepackages", lambda: 'n/a')())

# 1) Try vendor fallback (if you vendored package under repo/vendor)
VENDOR_DIR = ROOT / "vendor"
if str(VENDOR_DIR) not in sys.path:
    if VENDOR_DIR.exists():
        sys.path.insert(0, str(VENDOR_DIR))
        print("✅ Added vendor to sys.path:", VENDOR_DIR)
    else:
        print("ℹ️ vendor folder not found at:", VENDOR_DIR)

# 2) Try importing coinbase_advanced_py
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except Exception as e:
    print("❌ Failed to import coinbase_advanced_py:", type(e).__name__, e)
    # Diagnostic: show pip info for the package, installed packages, and vendor listing
    try:
        print("\n--- pip show coinbase-advanced-py ---")
        subprocess.run([sys.executable, "-m", "pip", "show", "coinbase-advanced-py"], check=False)
    except Exception as ex:
        print("pip show failed:", ex)
    try:
        print("\n--- pip list (top 40) ---")
        subprocess.run([sys.executable, "-m", "pip", "list", "--format=columns"], check=False)
    except Exception:
        pass
    print("\n--- Files in site-packages (sample) ---")
    # Attempt to show site-packages directories contents
    sp = None
    try:
        sp = site.getsitepackages()
    except Exception:
        sp = []
    for d in sp:
        print("site-packages dir:", d)
        try:
            entries = list(Path(d).glob("coinbase*"))[:30]
            for p in entries:
                print("  ", p)
        except Exception:
            pass
    # If vendor path exists, list it
    if VENDOR_DIR.exists():
        print("\n--- vendor dir listing ---")
        for p in sorted(VENDOR_DIR.glob("*"))[:200]:
            print("  ", p)
    else:
        print("\n(no vendor dir)")

    # Fail with helpful exit code — render will show logs
    raise SystemExit("Module coinbase_advanced_py not available. See diagnostics above.")

# 3) Load environment keys (Render: set env vars in service settings)
from dotenv import load_dotenv
try:
    load_dotenv()
    print("✅ Loaded .env (if present)")
except Exception:
    print("ℹ️ python-dotenv missing or .env absent (ok on Render)")

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SANDBOX = os.getenv("SANDBOX", "True").lower() in ("1", "true", "yes")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes")

if not API_KEY or not API_SECRET:
    print("⚠️ Missing API_KEY or API_SECRET environment variables!")
    if not DRY_RUN:
        raise SystemExit("Missing API keys and DRY_RUN is false. Exiting.")
    else:
        print("⚠️ Continuing in DRY_RUN mode (no live trades).")

# 4) Initialize client with safe handling
client = None
try:
    # coinbase_advanced_py may expose other constructors; use a safe try
    if hasattr(cb, "Client"):
        client = cb.Client(API_KEY or "fake", API_SECRET or "fake", sandbox=SANDBOX)
    else:
        # attempt common alternatives if library changed
        client = getattr(cb, "CoinbaseClient", None)
        if client is None:
            raise AttributeError("client constructor not found in coinbase_advanced_py")
        client = client(API_KEY or "fake", API_SECRET or "fake", sandbox=SANDBOX)
    print("✅ Coinbase client initialized ->", type(client))
except Exception as e:
    print("❌ Error initializing Coinbase client:", type(e).__name__, e)
    if not DRY_RUN:
        raise SystemExit("Cannot init client and not DRY_RUN. Exiting.")
    else:
        print("ℹ️ Continuing in DRY_RUN due to missing client initialization.")

# 5) Quick sanity call (best-effort)
try:
    if client:
        if hasattr(client, "get_account_balances"):
            print("💰 Balances:", client.get_account_balances())
        elif hasattr(client, "get_accounts"):
            print("💰 Accounts:", client.get_accounts())
        else:
            print("ℹ️ Client methods:", [m for m in dir(client) if not m.startswith("_")][:20])
    else:
        print("ℹ️ No client available (DRY_RUN).")
except Exception as e:
    print("ℹ️ Balance call failed:", e)

# 6) Main loop placeholder
try:
    while True:
        print(f"♥ Nija heartbeat — DRY_RUN={DRY_RUN}, SANDBOX={SANDBOX} — {time.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(30)
except KeyboardInterrupt:
    print("🛑 Exiting on user interrupt")
