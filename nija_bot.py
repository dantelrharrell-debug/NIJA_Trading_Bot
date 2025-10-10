#!/usr/bin/env python3
import os
import sys
import time
import traceback
from importlib import import_module

# -------- Add vendor folder if present (preferred if you vendor the package) --------
VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")
if os.path.isdir(VENDOR_DIR) and VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)
    print("✅ Added vendor folder to sys.path:", VENDOR_DIR)

# -------- Try to import coinbase_advanced_py, with fallbacks --------
PACKAGE_NAME = "coinbase_advanced_py"
PYPI_REQ = "coinbase-advanced-py==1.8.2"

def try_import():
    try:
        return import_module(PACKAGE_NAME)
    except Exception as e:
        return None

cb = try_import()
if cb is None:
    print("⚠️ coinbase_advanced_py not found in vendor or site-packages, attempting runtime install...")
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", PYPI_REQ])
        # try import again
        cb = try_import()
    except Exception:
        print("❌ Runtime pip install failed. Traceback:")
        traceback.print_exc()
        cb = None

if cb is None:
    raise SystemExit("❌ coinbase_advanced_py import FAILED. Add vendor/coinbase_advanced_py to your repo or ensure requirements.txt includes coinbase-advanced-py.")

print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))

# -------- Load environment & safety defaults --------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1","true","yes")
TRADE_SYMBOLS = os.getenv("TRADE_SYMBOLS", "BTC-USD,ETH-USD").split(",")
SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", "10"))

if not API_KEY or not API_SECRET:
    print("⚠️ Missing API_KEY or API_SECRET environment variables. Bot will run in read-only mode.")
    DRY_RUN = True

# -------- robust client constructor detection --------
client = None
client_errors = []

# Common constructor names we’ll try
possible_ctor_names = [
    "Client", "client", "CoinbaseClient", "CoinbaseAdvancedClient", "CoinbaseAdvanced", "APIClient"
]

for name in possible_ctor_names:
    try:
        ctor = getattr(cb, name)
        # attempt to construct with typical args (api_key, api_secret) — wrap in try/except
        try:
            client = ctor(API_KEY, API_SECRET)
        except TypeError:
            # maybe it takes keyword args
            try:
                client = ctor(api_key=API_KEY, api_secret=API_SECRET)
            except Exception:
                client = None
        except Exception:
            client = None
    except AttributeError:
        client = None

# If still none, show available names to help debugging
if client is None:
    print("⚠️ Could not instantiate client using common constructors. Listing available attributes of the package to help debug:")
    print(sorted([n for n in dir(cb) if not n.startswith("_")])[:200])
    print("Please check the package API (which constructor to use). Running in DRY_RUN (no trades).")
    DRY_RUN = True
else:
    print("🚀 Coinbase client object created:", type(client))

# -------- Demo: fetch balances or price (safe if DRY_RUN) --------
def safe_print_balances():
    try:
        # attempt to call common balance methods
        for fn in ("get_account_balances", "get_balances", "get_accounts"):
            if hasattr(client, fn):
                res = getattr(client, fn)()
                print("💰 Balances (via {}): {}".format(fn, res))
                return
        # fallback: check for product price method
        if hasattr(client, "get_product_price"):
            for s in TRADE_SYMBOLS:
                try:
                    print("📈 Price", s, ":", client.get_product_price(s))
                except Exception:
                    pass
    except Exception:
        print("❌ Error reading balances/prices:")
        traceback.print_exc()

if __name__ == "__main__":
    print("🔥 Starting Nija Trading Bot (DRY_RUN={})".format(DRY_RUN))
    # one-time demo check
    safe_print_balances()
    # main loop placeholder
    try:
        while True:
            # the real trading logic goes here; we keep a safe loop
            print("⏱ heartbeat — checking prices (DRY_RUN={})".format(DRY_RUN))
            if client and not DRY_RUN and hasattr(client, "place_order"):
                # example (very cautious): place a market buy (disabled by default)
                pass
            time.sleep(SLEEP_INTERVAL)
    except KeyboardInterrupt:
        print("🛑 Interrupted — exiting")
