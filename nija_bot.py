#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

"""
nija_bot.py
Robust Coinbase autodetector + safe fallback for Render.
Reads credentials from:
 - COINBASE_PEM  (PEM text, preferred)
 - or API_KEY and API_SECRET (legacy)
"""

import os
import traceback
from flask import Flask, jsonify

LIVE_TRADING = False
client = None

def log(*a, **k):
    print(*a, **k, flush=True)

# ---------------------------
# Credentials (from Render env)
# ---------------------------
COINBASE_PEM = os.getenv("COINBASE_PEM")     # full PEM content
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# ---------------------------
# Try coinbase-advanced-py (preferred)
# ---------------------------
try:
    from coinbase_advanced_py import CoinbaseAdvancedClient  # type: ignore
    HAVE_ADVANCED = True
    log("DEBUG: coinbase_advanced_py import OK")
except Exception:
    CoinbaseAdvancedClient = None
    HAVE_ADVANCED = False
    log("DEBUG: coinbase_advanced_py not importable")

# ---------------------------
# Try older-style 'coinbase' package (fallback)
# ---------------------------
try:
    import coinbase as cb_legacy  # type: ignore
    log("DEBUG: legacy 'coinbase' package import OK")
except Exception:
    cb_legacy = None
    log("DEBUG: legacy 'coinbase' package not importable")

# ---------------------------
# Attempt to initialize a real client (multiple strategies)
# ---------------------------
def _init_from_pem():
    """Write PEM to /tmp and try to initialize clients that accept a PEM file."""
    global client, LIVE_TRADING
    if not COINBASE_PEM:
        return False
    pem_path = "/tmp/my_coinbase_key.pem"
    try:
        with open(pem_path, "w") as f:
            f.write(COINBASE_PEM)
        log(f"✅ PEM written to {pem_path}")
    except Exception as e:
        log("❌ Failed to write PEM:", e)
        return False

    # 1) Try coinbase_advanced_py CoinbaseAdvancedClient(pem_file=...)
    if HAVE_ADVANCED and CoinbaseAdvancedClient is not None:
        try:
            client = CoinbaseAdvancedClient(pem_file=pem_path)
            LIVE_TRADING = True
            log("🟢 ✅ Live CoinbaseAdvancedClient initialized via PEM")
            return True
        except Exception as e:
            log("❌ CoinbaseAdvancedClient init failed:", type(e).__name__, e)
            log(traceback.format_exc())

    # 2) Try coinbase.legacy REST clients if available (some libs accept pem path)
    if cb_legacy is not None:
        try:
            if hasattr(cb_legacy, "rest"):
                rest_mod = getattr(cb_legacy, "rest")
                for cand in ("RESTClient", "RESTBase", "Client"):
                    if hasattr(rest_mod, cand):
                        cls = getattr(rest_mod, cand)
                        try:
                            inst = cls(pem_file=pem_path)
                            client = inst
                            LIVE_TRADING = True
                            log(f"🟢 ✅ Initialized legacy {cand} with pem_file kwarg")
                            return True
                        except Exception:
                            pass
        except Exception:
            log("DEBUG: legacy coinbase pem init attempts failed")
    return False

def _init_from_key_secret():
    """Try API_KEY / API_SECRET patterns."""
    global client, LIVE_TRADING
    if not (API_KEY and API_SECRET):
        return False

    # Try coinbase_advanced_py first
    if HAVE_ADVANCED and CoinbaseAdvancedClient is not None:
        try:
            try:
                client = CoinbaseAdvancedClient(api_key=API_KEY, api_secret=API_SECRET)
            except Exception:
                client = CoinbaseAdvancedClient(API_KEY, API_SECRET)
            LIVE_TRADING = True
            log("🟢 ✅ CoinbaseAdvancedClient initialized with API key/secret")
            return True
        except Exception as e:
            log("❌ CoinbaseAdvancedClient init with key/secret failed:", type(e).__name__, e)
            log(traceback.format_exc())

    # Try legacy coinbase.rest.RESTClient(API_KEY, API_SECRET)
    if cb_legacy is not None:
        try:
            if hasattr(cb_legacy, "rest"):
                rest_mod = getattr(cb_legacy, "rest")
                if hasattr(rest_mod, "RESTClient"):
                    try:
                        client = rest_mod.RESTClient(API_KEY, API_SECRET)
                        LIVE_TRADING = True
                        log("🟢 ✅ legacy RESTClient instantiated with API_KEY/API_SECRET")
                        return True
                    except Exception as e:
                        log("❌ RESTClient init failed:", type(e).__name__, e)
        except Exception:
            log("DEBUG: legacy coinbase key/secret init attempts failed")
    return False

# ---------------------------
# Initialize client
# ---------------------------
ok = _init_from_pem()
if not ok:
    ok = _init_from_key_secret()

if not ok:
    log("WARN: No live Coinbase client initialized; falling back to MockClient")
    LIVE_TRADING = False

# ---------------------------
# MockClient (safe)
# ---------------------------
class MockClient:
    def get_account_balances(self):
        return {"USD": 10000.0, "BTC": 0.05}
    def place_order(self, *a, **k):
        raise RuntimeError("DRY RUN: MockClient refuses to place orders")

if not LIVE_TRADING or client is None:
    client = MockClient()

# ---------------------------
# Read balances (safe)
# ---------------------------
try:
    balances = client.get_account_balances()
    log(f"💰 Starting balances: {balances}")
except Exception as e:
    balances = {"error": str(e)}
    log("❌ Error reading balances:", type(e).__name__, e)

log(f"🔒 LIVE_TRADING = {LIVE_TRADING}")

# ---------------------------
# Minimal Flask app
# ---------------------------
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
