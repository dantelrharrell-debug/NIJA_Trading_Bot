import pkgutil, subprocess, sys, traceback
try:
    out = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True, stderr=subprocess.STDOUT)
except Exception as e:
    out = f"pip freeze failed: {e}"
print("---- pip freeze (top 200) ----")
print(out)
print("---- pkgutil.iter_modules (first 200) ----")
print([m.name for m in pkgutil.iter_modules()][:200])
try:
    import importlib
    for name in ("coinbase_advanced_py","coinbase_advanced","coinbase"):
        try:
            mod = importlib.import_module(name)
            print("Imported", name, "->", mod)
        except Exception:
            print("Failed to import", name)
            traceback.print_exc()
except Exception:
    print("debug import check failed")

#!/usr/bin/env python3
"""
nija_bot.py - NIJA Trading Bot (single-file, Render-ready)

Behavior:
 - Attempts to detect/install the correct Coinbase client import name at runtime.
 - Starts a Flask heartbeat (binds to $PORT).
 - Spawns a background bot thread that fetches balances periodically.
 - Will only place orders if LIVE_TRADING=true in env (defaults to False).
 - Prints detailed diagnostic logs to help troubleshoot missing modules.
"""
import os
import sys
import time
import threading
import traceback
import importlib
import pkgutil
from typing import Any, Callable, Optional

from flask import Flask

# ---------- Config ----------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
LIVE_TRADING = os.getenv("LIVE_TRADING", "false").lower() == "true"
PORT = int(os.getenv("PORT", 10000))
SLEEP_SECONDS = int(os.getenv("SLEEP_SECONDS", 60))

app = Flask(__name__)

@app.route("/")
def heartbeat():
    return "NIJA BOT alive ✅"

def debug_installed_packages(head=60):
    try:
        import subprocess
        out = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True, stderr=subprocess.STDOUT)
        lines = out.strip().splitlines()
        return lines[:head]
    except Exception:
        # fallback to pkgutil listing
        return [m.name for m in pkgutil.iter_modules()][:head]

# ---------- Coinbase import detection ----------
def find_coinbase_client():
    """
    Try a number of likely module names and attribute locations to find a usable Client class.
    Returns (ClientClass, import_path_string) or (None, None)
    """
    candidates = [
        ("coinbase_advanced_py", ["Client", "client.Client"]),
        ("coinbase_advanced", ["Client", "client.Client"]),
        ("coinbase", ["Client", "client.Client"]),
        # Add more candidate roots if necessary
    ]
    for root, attrs in candidates:
        try:
            mod = importlib.import_module(root)
        except ModuleNotFoundError:
            # try next candidate
            continue
        except Exception:
            # some other error while importing; surface debug info
            print(f"⚠️ import {root} raised an exception:", traceback.format_exc())
            continue

        # Try attribute variations
        for attr_path in attrs:
            parts = attr_path.split(".")
            cur = mod
            ok = True
            for p in parts:
                if not hasattr(cur, p):
                    ok = False
                    break
                cur = getattr(cur, p)
            if ok:
                # cur should be the Client class or factory
                print(f"✅ Found Coinbase client: {root}.{attr_path}")
                return cur, f"{root}.{attr_path}"

        # As a last attempt, maybe a submodule 'client' exists
        try:
            sub = importlib.import_module(f"{root}.client")
            if hasattr(sub, "Client"):
                print(f"✅ Found Coinbase client: {root}.client.Client")
                return getattr(sub, "Client"), f"{root}.client.Client"
        except Exception:
            pass

    return None, None

# Provide a small safe adapter that exposes the methods we call,
# so rest of engine can operate without deep coupling to library internals.
class MockClient:
    def __init__(self, *a, **k):
        print("⚠️ MockClient created — real Coinbase client not available.")
    def get_account_balances(self):
        return []
    def get_spot_price(self, symbol):
        # return minimal shape used in code
        return {"amount": "0"}
    def get_historic_rates(self, symbol, granularity=60):
        # return some fake candles: [time, low, high, open, close, volume]
        now = int(time.time())
        return [[now - i*60, 0, 0, 0, 0, 0] for i in range(100)]
    def place_order(self, **kwargs):
        raise RuntimeError("LIVE_TRADING disabled or real client not available")

# ---------- Initialize Coinbase client ----------
ClientClass, import_path = find_coinbase_client()
coinbase_client = None
if ClientClass is None:
    print("❌ No Coinbase client module found. Installed packages (top of pip freeze):")
    for line in debug_installed_packages(100):
        print("   ", line)
    print("ℹ️ The package name provided in requirements should create an importable module like 'coinbase_advanced_py'.")
    # Use mock client so the server still runs and the bot loop doesn't crash
    coinbase_client = MockClient()
else:
    if not API_KEY or not API_SECRET:
        print("❌ API_KEY/API_SECRET not set. Please set them in Render environment variables.")
        # Still create a client if implementation supports unauth calls, otherwise use mock.
        try:
            coinbase_client = ClientClass()
            print("⚠️ Client created without keys (some methods may be limited).")
        except Exception as e:
            print("⚠️ Failed to create client without keys:", e)
            coinbase_client = MockClient()
    else:
        try:
            # try constructing in a couple ways, graceful fallback
            try:
                coinbase_client = ClientClass(API_KEY, API_SECRET)
            except TypeError:
                # maybe it expects keyword names
                coinbase_client = ClientClass(api_key=API_KEY, api_secret=API_SECRET)
            print(f"✅ Coinbase client created using {import_path}")
        except Exception as e:
            print("❌ Failed to create Coinbase client:", type(e).__name__, e)
            print("Traceback:")
            traceback.print_exc()
            coinbase_client = MockClient()

# ---------- Helpers (simple safe versions) ----------
def safe_get_balances():
    try:
        return coinbase_client.get_account_balances()
    except Exception as e:
        print("❌ get_account_balances error:", type(e).__name__, e)
        return []

def safe_get_spot_price(sym):
    try:
        p = coinbase_client.get_spot_price(sym)
        # handle both dict and object shapes
        if isinstance(p, dict) and "amount" in p:
            return float(p["amount"])
        # try attributes
        if hasattr(p, "amount"):
            return float(getattr(p, "amount"))
        return float(p)
    except Exception as e:
        print("❌ get_spot_price error for", sym, type(e).__name__, e)
        return 0.0

# Example trading decision logic (very simple and safe)
def bot_cycle_once():
    balances = safe_get_balances()
    print("Balances snapshot:", balances)
    for sym in ("BTC", "ETH"):
        price = safe_get_spot_price(sym)
        print(f"{sym} spot price: {price}")

# ---------- Bot background thread ----------
def bot_loop():
    print("🟢 Bot thread starting; LIVE_TRADING =", LIVE_TRADING)
    if not API_KEY or not API_SECRET:
        print("⚠️ API keys missing — bot will not perform live trades.")
    while True:
        try:
            bot_cycle_once()
        except Exception as e:
            print("❌ Error in bot loop:", type(e).__name__, str(e))
            traceback.print_exc()
        time.sleep(max(5, SLEEP_SECONDS))

# Start background thread
thread = threading.Thread(target=bot_loop, daemon=True)
thread.start()

# ---------- Main runner (Flask) ----------
if __name__ == "__main__":
    print("🚀 NIJA BOT starting; debug info:")
    print("  Python:", sys.executable)
    print("  sys.path head:", sys.path[:6])
    print("  Detected Coinbase client import:", import_path)
    print("  LIVE_TRADING:", LIVE_TRADING)
    print("  PORT:", PORT)
    # Bind to 0.0.0.0 so Render can reach it
    app.run(host="0.0.0.0", port=PORT)
