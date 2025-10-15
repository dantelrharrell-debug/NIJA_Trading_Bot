import sys
print("Python executable:", sys.executable)
print("sys.path:")
for p in sys.path:
    print("  ", p)

#!/usr/bin/env python3
"""
nija_bot.py
Robust Coinbase autodetector + safe fallback for Render.
Ensures coinbase-advanced-py is loaded from virtualenv and handles PEM/API credentials.
"""

import os
import sys
import traceback
from dotenv import load_dotenv
from flask import Flask, jsonify

# -------------------------------------------------
# Ensure Render virtualenv packages are on sys.path
# -------------------------------------------------
VENV_SITE_PACKAGES = "/opt/render/project/src/.venv/lib/python3.13/site-packages"
if VENV_SITE_PACKAGES not in sys.path:
    sys.path.insert(0, VENV_SITE_PACKAGES)

# -------------------------------------------------
# Load environment variables
# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# Logging helper
# -------------------------------------------------
def log(*args, **kwargs):
    print(*args, **kwargs, flush=True)

# -------------------------------------------------
# Attempt to import coinbase_advanced_py
# -------------------------------------------------
try:
    import coinbase_advanced_py as cb
    HAVE_ADVANCED = True
    log("✅ coinbase_advanced_py imported successfully")
except Exception as e:
    HAVE_ADVANCED = False
    log("❌ coinbase_advanced_py import failed:", e)

# -------------------------------------------------
# Attempt legacy coinbase package
# -------------------------------------------------
try:
    import coinbase as cb_legacy
    log("ℹ️ legacy 'coinbase' package import OK")
except Exception:
    cb_legacy = None
    log("⚠️ legacy 'coinbase' package not importable")

# -------------------------------------------------
# Read credentials
# -------------------------------------------------
COINBASE_PEM = os.getenv("COINBASE_PEM")          # full PEM content
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSPHRASE = os.getenv("API_PASSPHRASE")

PEM_PATH = "/tmp/my_coinbase_key.pem"
if COINBASE_PEM:
    try:
        with open(PEM_PATH, "w") as f:
            f.write(COINBASE_PEM)
        log(f"✅ PEM written to {PEM_PATH}")
    except Exception as e:
        log("❌ Failed to write PEM:", e)

# -------------------------------------------------
# Initialize client
# -------------------------------------------------
LIVE_TRADING = False
client = None

def _init_from_pem():
    global client, LIVE_TRADING
    if not COINBASE_PEM:
        return False

    if HAVE_ADVANCED:
        try:
            client = cb.CoinbaseAdvancedClient(pem_file=PEM_PATH)
            LIVE_TRADING = True
            log("🟢 ✅ Live CoinbaseAdvancedClient initialized via PEM")
            return True
        except Exception as e:
            log("❌ CoinbaseAdvancedClient init via PEM failed:", type(e).__name__, e)
            log(traceback.format_exc())

    if cb_legacy is not None:
        try:
            if hasattr(cb_legacy, "rest"):
                rest_mod = getattr(cb_legacy, "rest")
                for cand in ("RESTClient", "RESTBase", "Client"):
                    if hasattr(rest_mod, cand):
                        try:
                            client = getattr(rest_mod, cand)(pem_file=PEM_PATH)
                            LIVE_TRADING = True
                            log(f"🟢 ✅ Legacy {cand} initialized via PEM")
                            return True
                        except Exception:
                            continue
        except Exception:
            log("DEBUG: Legacy coinbase PEM init attempts failed")
    return False

def _init_from_keys():
    global client, LIVE_TRADING
    if not (API_KEY and API_SECRET):
        return False

    if HAVE_ADVANCED:
        try:
            client = cb.CoinbaseAdvancedClient(api_key=API_KEY, api_secret=API_SECRET, passphrase=API_PASSPHRASE)
            LIVE_TRADING = True
            log("🟢 ✅ CoinbaseAdvancedClient initialized with API keys")
            return True
        except Exception as e:
            log("❌ CoinbaseAdvancedClient init with API keys failed:", type(e).__name__, e)
            log(traceback.format_exc())

    if cb_legacy is not None:
        try:
            if hasattr(cb_legacy, "rest") and hasattr(cb_legacy.rest, "RESTClient"):
                client = cb_legacy.rest.RESTClient(API_KEY, API_SECRET)
                LIVE_TRADING = True
                log("🟢 ✅ Legacy RESTClient instantiated with API_KEY/API_SECRET")
                return True
        except Exception as e:
            log("❌ Legacy RESTClient init failed:", type(e).__name__, e)
    return False

# Try PEM first, then keys
ok = _init_from_pem() or _init_from_keys()

# Fallback MockClient
class MockClient:
    def get_account_balances(self):
        return {"USD": 10000.0, "BTC": 0.05}

    def place_order(self, *a, **k):
        raise RuntimeError("DRY RUN: MockClient refuses to place orders")

if not ok or client is None:
    client = MockClient()
    LIVE_TRADING = False
    log("⚠️ Using MockClient (no live trading)")

# -------------------------------------------------
# Fetch balances
# -------------------------------------------------
try:
    balances = client.get_account_balances()
    log(f"💰 Starting balances: {balances}")
except Exception as e:
    balances = {"error": str(e)}
    log("❌ Error reading balances:", type(e).__name__, e)

log(f"🔒 LIVE_TRADING = {LIVE_TRADING}")

# -------------------------------------------------
# Minimal Flask server
# -------------------------------------------------
app = Flask("nija_bot")

@app.route("/")
def home():
    return jsonify({
        "status": "NIJA Bot is running!",
        "LIVE_TRADING": LIVE_TRADING,
        "balances": balances
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    log(f"🚀 Starting NIJA Bot Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
