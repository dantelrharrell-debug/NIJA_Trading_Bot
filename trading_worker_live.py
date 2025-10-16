#!/usr/bin/env python3
import os
import json
from dotenv import load_dotenv
from coinbase_advanced_py import CoinbaseClient
from flask import Flask, request, jsonify

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM_B64 = os.getenv("API_PEM_B64")
PASSPHRASE = os.getenv("PASSPHRASE")  # optional
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"

# Always disable mock if live trading
USE_MOCK = not LIVE_TRADING
SANDBOX = USE_MOCK

# -----------------------------
# Initialize Coinbase client
# -----------------------------
client = CoinbaseClient(
    api_key=API_KEY,
    api_secret=API_SECRET,
    passphrase=PASSPHRASE,
    pem_b64=API_PEM_B64,
    sandbox=SANDBOX
)

print(f"✅ Coinbase client initialized. Sandbox={SANDBOX}, Live={LIVE_TRADING}")

# -----------------------------
# Optional: Print account balances
# -----------------------------
try:
    accounts = client.get_accounts()
    print("Your Coinbase balances:")
    for acc in accounts:
        print(f"{acc['currency']}: {acc['balance']}")
except Exception as e:
    print("⚠️ Could not fetch accounts:", e)

# -----------------------------
# Flask app for TradingView webhooks
# -----------------------------
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")

    if secret != TV_WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 401

    signal = data.get("signal")
    pair = data.get("pair", "BTC-USD")
    amount = data.get("amount", 0.001)

    print(f"🔔 Received signal: {signal} for {pair}, amount={amount}")

    if USE_MOCK:
        print("🧪 Mock trade executed (no real funds).")
    else:
        try:
            if signal == "buy":
                order = client.buy(pair, amount)
            elif signal == "sell":
                order = client.sell(pair, amount)
            else:
                order = None
                print("⚠️ Unknown signal received.")
            print("✅ Order response:", order)
        except Exception as e:
            print("❌ Trade failed:", e)

    return jsonify({"status": "ok"})

# -----------------------------
# Run Flask server
# -----------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
