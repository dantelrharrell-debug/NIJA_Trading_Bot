#!/usr/bin/env python3
import os
import sys
import traceback
import json
import time
from flask import Flask

# --------------------------
# Coinbase advanced client
# --------------------------
import coinbase_advanced_py as cb  # <--- put it here

# --------------------------
# Load API keys from environment
# --------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set")

# Initialize Coinbase client
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("✅ Coinbase client connected — LIVE_TRADING=True")
except Exception as e:
    print("❌ Failed to initialize live Coinbase client:", e)
    print("⚠️ Running in mock mode — LIVE_TRADING=False")
    from mock_client import MockClient  # assuming you have a mock client file
    client = MockClient()

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
    "coinbase_advanced_py",
    "coinbase_advanced",
    "coinbase",
    "coinbase_advanced_py_client",
    "coinbasepro",
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
# Routes
# -------------------
@app.route("/balances", methods=["GET"])
def get_balances():
    balances = client.get_account_balances()
    return jsonify(balances)

@app.route("/order", methods=["POST"])
def place_order_route():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Empty payload"}), 400

        symbol = data.get("symbol")
        side = data.get("side")
        size = data.get("size")
        order_type = data.get("order_type", "market")
        price = data.get("price", None)

        if not symbol or not side or not size:
            return jsonify({"error": "Missing required fields: symbol, side, size"}), 400

        # Optional: validate TradingView strategy if sent
        strategy = data.get("strategy")
        if strategy == "VWAP+RSI":
            # Implement thresholds check if needed
            pass

        result = client.place_order(
            symbol=symbol,
            side=side,
            size=size,
            price=price,
            order_type=order_type
        )

        return jsonify({"status": "success", "order": result})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

# -------------------
# Start Flask app
# -------------------
if __name__ == "__main__":
    print("🚀 Starting NIJA Bot...")
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
