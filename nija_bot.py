#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# -------------------
# Standard imports
# -------------------
import os
import sys
import traceback
import importlib
from flask import Flask, request, jsonify
import threading
import time
import json

# -------------------
# Interpret USE_MOCK strictly
# Only '1', 'true', 'yes' (case-insensitive) enable mock mode
# -------------------
_raw = os.getenv("USE_MOCK", "")
USE_MOCK = _raw.strip().lower() in ("1", "true", "yes")

# -------------------
# Defaults
# -------------------
client = None
LIVE_TRADING = False

# -------------------
# Robust Coinbase import + client initialization
# -------------------
_coinbase_candidates = [
    "coinbase_advanced_py",   # expected
    "coinbase_advanced",      # possible alternate
    "coinbase",               # generic
    "coinbase_advanced_py_client",
    "coinbasepro",            # sometimes used by other libs
]

_coinbase_module = None
_coinbase_name = None

if not USE_MOCK:
    for _name in _coinbase_candidates:
        try:
            _mod = importlib.import_module(_name)
            _coinbase_module = _mod
            _coinbase_name = _name
            print(f"✅ Imported Coinbase module using '{_name}'")
            break
        except Exception:
            pass  # try next candidate

    if _coinbase_module is None:
        print("❌ Coinbase module not found under tried names:", _coinbase_candidates)
        USE_MOCK = True

if not USE_MOCK and _coinbase_module:
    API_KEY = os.getenv("API_KEY", "")
    API_SECRET = os.getenv("API_SECRET", "")

    if not API_KEY or not API_SECRET:
        print("⚠️ API_KEY or API_SECRET not set — cannot initialize live client.")
        USE_MOCK = True
    else:
        try:
            # Try common constructors
            for ctor in ("Client", "ClientV2", "CoinbaseClient"):
                if hasattr(_coinbase_module, ctor):
                    try:
                        client = getattr(_coinbase_module, ctor)(API_KEY, API_SECRET)
                        LIVE_TRADING = True
                        print(f"🚀 Initialized client via {_coinbase_name}.{ctor}()")
                        break
                    except Exception as e:
                        print(f"⚠️ {_coinbase_name}.{ctor}() raised:", e)

            # Try factory function
            if client is None and hasattr(_coinbase_module, "create_client"):
                try:
                    client = _coinbase_module.create_client(API_KEY, API_SECRET)
                    LIVE_TRADING = True
                    print(f"🚀 Initialized client via {_coinbase_name}.create_client()")
                except Exception as e:
                    print(f"⚠️ {_coinbase_name}.create_client() raised:", e)

            # Last attempt: module callable
            if client is None and callable(_coinbase_module):
                try:
                    client = _coinbase_module(API_KEY, API_SECRET)
                    LIVE_TRADING = True
                    print(f"🚀 Initialized client by calling module {_coinbase_name}()")
                except Exception as e:
                    print(f"⚠️ Calling {_coinbase_name}() raised:", e)

            if client is None:
                raise RuntimeError("Could not initialize client from imported module (no usable constructor)")

        except Exception as exc:
            print("❌ Failed to initialize live Coinbase client:", exc)
            traceback.print_exc()
            USE_MOCK = True

# -------------------
# MockClient for fallback / testing
# -------------------
if USE_MOCK or client is None:
    class MockClient:
        def __init__(self):
            self.balances = {'USD': 10000.0, 'BTC': 0.05, 'ETH': 0.3}
            print("🧪 MockClient initialized with balances:", self.balances)

        def get_account_balances(self):
            return self.balances

        def place_order(self, symbol, side, size, price=None, order_type="market"):
            print(f"🧪 Mock order: {side} {size} {symbol} @ {price if price else 'market'}")
            return {"id": "mock_order_123", "status": "filled"}

    client = MockClient()
    LIVE_TRADING = False
    print("⚠️ Running in mock mode — Coinbase client not connected.")

# -------------------
# Final state summary
# -------------------
if LIVE_TRADING:
    print(f"🟢 Live Coinbase client ready. LIVE_TRADING={LIVE_TRADING}")
else:
    print("⚠️ Using MockClient. LIVE_TRADING=False")

# -------------------
# Flask app
# -------------------
app = Flask(__name__)

# -------------------
# Position sizing
# -------------------
MIN_PCT = 0.02  # 2%
MAX_PCT = 0.10  # 10%

def calculate_position_size(account_usd, pct=0.05):
    return max(account_usd * pct, 0)

# -------------------
# Trading endpoint for TradingView alerts
# -------------------
@app.route("/order", methods=["POST"])
def place_order_route():
    try:
        data = request.json
        symbol = data.get("symbol")
        side = data.get("side")
        size_pct = data.get("size_pct", 0.05)  # default 5% of account
        account_balances = client.get_account_balances()
        account_usd = account_balances.get("USD", 0)
        size = calculate_position_size(account_usd, size_pct)

        price = data.get("price", None)
        order_type = data.get("order_type", "market")

        result = client.place_order(symbol, side, size, price, order_type)
        print(f"💰 Executed {side.upper()} {size} {symbol} @ {price if price else 'market'}")
        return jsonify({"status": "success", "order": result})
    except Exception as e:
        print("❌ Error placing order:", e)
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# -------------------
# Check balances endpoint
# -------------------
@app.route("/balances", methods=["GET"])
def get_balances():
    try:
        balances = client.get_account_balances()
        return jsonify(balances)
    except Exception as e:
        print("❌ Error fetching balances:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

# -------------------
# Start Flask app (threaded)
# -------------------
if __name__ == "__main__":
    print("🚀 Starting NIJA Bot...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
