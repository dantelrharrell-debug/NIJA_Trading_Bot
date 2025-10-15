#!/usr/bin/env python3
# nija_bot.py — Coinbase REST client with safe PEM handling + Flask

import os
import traceback
from flask import Flask, jsonify

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")  # path to PEM file

LIVE_TRADING = False
client = None

def debug(msg):
    print("DEBUG:", msg)

# ------------------------
# Check PEM file
# ------------------------
if API_SECRET:
    if not os.path.isfile(API_SECRET):
        debug(f"❌ PEM file not found at {API_SECRET}")
        API_SECRET = None
    else:
        debug(f"✅ PEM file found at {API_SECRET}")
else:
    debug("❌ API_SECRET not set")

# ------------------------
# Attempt Coinbase REST client
# ------------------------
try:
    if API_KEY and API_SECRET:
        from coinbase.rest import RESTClient
        debug("Attempting RESTClient instantiation...")
        client = RESTClient(API_KEY, API_SECRET)
        LIVE_TRADING = True
        debug("✅ RESTClient instantiated. LIVE_TRADING=True")
except Exception as e:
    debug(f"RESTClient failed: {type(e).__name__} {e}")
    debug(traceback.format_exc())
    client = None
    LIVE_TRADING = False

# ------------------------
# Fallback to MockClient
# ------------------------
if not LIVE_TRADING or client is None:
    debug("⚠️ Falling back to MockClient")
    class MockClient:
        def get_account_balances(self):
            return {"USD": 10000.0, "BTC": 0.05}

        def place_order(self, *a, **k):
            raise RuntimeError("DRY RUN: MockClient refuses to place orders")

    client = MockClient()

# ------------------------
# Read balances
# ------------------------
try:
    balances = client.get_account_balances()
except Exception as e:
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
