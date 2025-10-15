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
# Config
# -------------------
USE_MOCK = os.getenv("USE_MOCK", "").strip().lower() in ("1", "true", "yes")
API_KEY = os.getenv("API_KEY", "")
API_SECRET = os.getenv("API_SECRET", "")

client = None
LIVE_TRADING = False

# -------------------
# Coinbase client initialization
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
    for name in _coinbase_candidates:
        try:
            _mod = importlib.import_module(name)
            _coinbase_module = _mod
            _coinbase_name = name
            print(f"✅ Imported Coinbase module using '{name}'")
            break
        except Exception:
            continue

    if _coinbase_module is None:
        print("❌ No Coinbase module found. Falling back to mock.")
        USE_MOCK = True

# Initialize live client
if not USE_MOCK and _coinbase_module and API_KEY and API_SECRET:
    try:
        # Try standard constructors
        for ctor in ("Client", "ClientV2", "CoinbaseClient"):
            if hasattr(_coinbase_module, ctor):
                client = getattr(_coinbase_module, ctor)(API_KEY, API_SECRET)
                LIVE_TRADING = True
                print(f"🚀 Initialized live client via {_coinbase_name}.{ctor}()")
                break

        # Try factory function
        if client is None and hasattr(_coinbase_module, "create_client"):
            client = _coinbase_module.create_client(API_KEY, API_SECRET)
            LIVE_TRADING = True
            print(f"🚀 Initialized live client via {_coinbase_name}.create_client()")

        # Try calling module directly
        if client is None and callable(_coinbase_module):
            client = _coinbase_module(API_KEY, API_SECRET)
            LIVE_TRADING = True
            print(f"🚀 Initialized live client by calling {_coinbase_name}()")

        if client is None:
            raise RuntimeError("No usable constructor found for Coinbase client.")

    except Exception as e:
        print("❌ Failed to initialize live Coinbase client:", e)
        USE_MOCK = True
        client = None

# -------------------
# Fallback MockClient
# -------------------
if USE_MOCK or client is None:
    class MockClient:
        def __init__(self):
            self.balances = {"USD": 10000.0, "BTC": 0.05, "ETH": 0.3}
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
# Status summary
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
    try:
        balances = client.get_account_balances()
        return jsonify(balances)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

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

        # Optional: validate strategy
        strategy = data.get("strategy")
        if strategy == "VWAP+RSI":
            # Placeholder for strategy validation
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
# Start Flask server
# -------------------
if __name__ == "__main__":
    print("🚀 Starting NIJA Bot...")
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
