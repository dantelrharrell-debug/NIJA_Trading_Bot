#!/usr/bin/env python3
# nija_bot.py — Coinbase Advanced REST client + safe Mock fallback

import os
import time
import hmac
import json
import hashlib
import requests
from flask import Flask, jsonify

# ----------------------
# Load environment variables
# ----------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSPHRASE = os.getenv("API_PASSPHRASE")  # optional depending on key type
LIVE_TRADING = False

BASE_URL = "https://api.exchange.coinbase.com"  # REST base for Advanced API

# ----------------------
# Debug function
# ----------------------
def debug(msg):
    print("DEBUG:", msg)

# ----------------------
# Simple REST client
# ----------------------
class CoinbaseRESTClient:
    def __init__(self, api_key, api_secret, api_passphrase=None, dry_run=True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.dry_run = dry_run

    def _get_headers(self, method, path, body=""):
        timestamp = str(int(time.time()))
        message = timestamp + method + path + body
        secret_bytes = self.api_secret.encode("utf-8")
        signature = hmac.new(secret_bytes, message.encode("utf-8"), hashlib.sha256).hexdigest()
        headers = {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": signature,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }
        if self.api_passphrase:
            headers["CB-ACCESS-PASSPHRASE"] = self.api_passphrase
        return headers

    def _request(self, method, path, body=""):
        url = BASE_URL + path
        headers = self._get_headers(method, path, body)
        if self.dry_run:
            debug(f"DRY_RUN {_request.__name__}: {method} {url} body={body}")
            return {}
        try:
            if method == "GET":
                r = requests.get(url, headers=headers)
            elif method == "POST":
                r = requests.post(url, headers=headers, data=body)
            else:
                raise ValueError("Unsupported method")
            r.raise_for_status()
            return r.json()
        except Exception as e:
            debug(f"REST request failed: {type(e).__name__} {e}")
            return {}

    # ----------------------
    # Public API methods
    # ----------------------
    def get_account_balances(self):
        return self._request("GET", "/accounts")

    def place_order(self, product_id="BTC-USD", side="buy", size="0.001", price=None, order_type="limit"):
        if self.dry_run:
            debug(f"DRY_RUN place_order: {side} {size} {product_id} price={price}")
            return {"status": "dry_run"}
        body = {
            "type": order_type,
            "side": side,
            "product_id": product_id,
            "size": size
        }
        if price and order_type == "limit":
            body["price"] = str(price)
        return self._request("POST", "/orders", json.dumps(body))

# ----------------------
# Initialize client
# ----------------------
if API_KEY and API_SECRET:
    client = CoinbaseRESTClient(API_KEY, API_SECRET, api_passphrase=API_PASSPHRASE, dry_run=True)
    LIVE_TRADING = True
    debug("✅ REST client initialized (dry_run=True by default)")
else:
    debug("❌ No API credentials found; using MockClient")

# ----------------------
# Fallback MockClient
# ----------------------
if not LIVE_TRADING or client is None:
    class MockClient:
        def get_account_balances(self):
            return {'USD': 10000.0, 'BTC': 0.05}
        def place_order(self, *a, **k):
            debug(f"DRY_RUN MockClient place_order args={a} kwargs={k}")
            return {"status": "dry_run"}
    client = MockClient()
    LIVE_TRADING = False

# ----------------------
# Print starting balances
# ----------------------
try:
    balances = client.get_account_balances()
except Exception as e:
    debug(f"Error reading balances: {type(e).__name__} {e}")
    balances = {"error": str(e)}

print(f"💰 Starting balances: {balances}")
print(f"🔒 LIVE_TRADING = {LIVE_TRADING}")

# ----------------------
# Flask setup
# ----------------------
app = Flask("nija_bot")

@app.route("/")
def home():
    return jsonify({
        "status": "NIJA Bot is running!",
        "LIVE_TRADING": LIVE_TRADING,
        "balances": balances
    })

# ----------------------
# Start Flask server
# ----------------------
if __name__ == "__main__":
    print("🚀 Starting NIJA Bot Flask server...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
