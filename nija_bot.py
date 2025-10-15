#!/usr/bin/env python3
import os
import sys
import traceback
import json
from flask import Flask, jsonify

# -------------------------------
# Coinbase PEM / Live trading setup
# -------------------------------
try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    print("❌ coinbase_advanced_py not found. Using MockClient.")
    cb = None

PEM_PATH = "/tmp/my_coinbase_key.pem"
PEM_CONTENT = os.getenv("COINBASE_PEM")

if PEM_CONTENT and cb:
    with open(PEM_PATH, "w") as f:
        f.write(PEM_CONTENT)
    try:
        client = cb.Client(api_key_path=PEM_PATH)
        LIVE_TRADING = True
        print("✅ Live Coinbase client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Coinbase client: {e}")
        cb = None
else:
    cb = None

# -------------------------------
# Fallback MockClient if live fails
# -------------------------------
if cb is None:
    print("⚠️ Using MockClient")
    class MockClient:
        def get_account_balances(self):
            return {"USD": 10000.0, "BTC": 0.05}
    client = MockClient()
    LIVE_TRADING = False

# -------------------------------
# Check starting balances
# -------------------------------
balances = client.get_account_balances()
print(f"💰 Starting balances: {balances}")
print(f"🔒 LIVE_TRADING = {LIVE_TRADING}")

# -------------------------------
# Flask server setup
# -------------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"status": "NIJA Bot is running", "balances": balances})

@app.route("/balances")
def get_balances():
    return jsonify({"balances": client.get_account_balances(), "live_trading": LIVE_TRADING})

# -------------------------------
# Start Flask server
# -------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 Starting NIJA Bot Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
