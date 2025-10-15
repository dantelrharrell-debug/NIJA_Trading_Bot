#!/usr/bin/env python3
# nija_bot.py — Coinbase RESTClient ready + safe fallback

import os
import importlib
import inspect
import traceback
from flask import Flask, jsonify

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

LIVE_TRADING = False
client = None

def debug(msg):
    print("DEBUG:", msg)

# ------------------------
# MockClient fallback
# ------------------------
class MockClient:
    def get_account_balances(self):
        return {'USD': 10000.0, 'BTC': 0.05}

    def get_accounts(self):
        return {'data': [
            {'currency': 'USD', 'balance': {'amount': '10000.0'}},
            {'currency': 'BTC', 'balance': {'amount': '0.05'}}
        ]}

    def place_order(self, *a, **k):
        raise RuntimeError("DRY RUN: MockClient refuses to place orders")

# ------------------------
# Try to load coinbase.rest.RESTClient
# ------------------------
try:
    cb = importlib.import_module("coinbase")
    rest_mod = importlib.import_module("coinbase.rest")
    debug(f"found REST module: {rest_mod}")

    if API_KEY and API_SECRET and hasattr(rest_mod, "RESTClient"):
        debug("attempting RESTClient instantiation")
        try:
            client = rest_mod.RESTClient(API_KEY, API_SECRET)
            LIVE_TRADING = True
            debug("✅ RESTClient instantiated. LIVE_TRADING=True")
        except Exception as e:
            debug(f"RESTClient instantiation failed: {type(e).__name__} {e}")
            client = MockClient()
            LIVE_TRADING = False
    else:
        debug("RESTClient not available or API keys missing")
        client = MockClient()
except Exception as e:
    debug(f"Coinbase RESTClient load failed: {type(e).__name__} {e}")
    client = MockClient()

# ------------------------
# Fetch balances
# ------------------------
try:
    balances = {}
    if LIVE_TRADING and hasattr(client, "get_accounts"):
        raw_accounts = client.get_accounts()
        # coinbase.rest.RESTClient returns dict with 'data' list
        for acc in raw_accounts.get('data', []):
            balances[acc['currency']] = float(acc['balance']['amount'])
    else:
        # fallback for MockClient or missing get_accounts
        balances = client.get_account_balances()
except Exception as e:
    debug(f"Error reading balances: {type(e).__name__} {e}")
    balances = {"error": str(e)}

print(f"💰 Starting balances: {balances}")
print(f"🔒 LIVE_TRADING = {LIVE_TRADING}")

# ------------------------
# Flask setup
# ------------------------
app = Flask("nija_bot")

@app.route("/")
def home():
    return jsonify({
        "status": "NIJA Bot is running!",
        "LIVE_TRADING": LIVE_TRADING,
        "balances": balances
    })

# ------------------------
# Start Flask server
# ------------------------
if __name__ == "__main__":
    print("🚀 Starting NIJA Bot Flask server...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
