#!/usr/bin/env python3
# 🥷 Nija Bot - Fully Live Coinbase Version
# ✅ Ready for Render and live trading

import os
import traceback
from flask import Flask, request, jsonify

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

# Try importing Coinbase library
try:
    import coinbase_advanced_py as cb
    COINBASE_OK = True
except ModuleNotFoundError:
    COINBASE_OK = False
    print("❌ Coinbase LIVE connection FAILED: No module named 'coinbase_advanced_py'")

app = Flask(__name__)

# -------- Coinbase Client Setup --------
if COINBASE_OK:
    try:
        API_KEY = os.getenv("COINBASE_API_KEY")
        API_SECRET = os.getenv("COINBASE_API_SECRET")
        COINBASE = cb.Client(api_key=API_KEY, api_secret=API_SECRET)
        print("✅ Coinbase client initialized.")
    except Exception as e:
        COINBASE_OK = False
        print("❌ Failed to initialize Coinbase client:", e)

# -------- Home route --------
@app.route("/")
def home():
    if COINBASE_OK:
        return "🥷 Nija Bot is LIVE and Coinbase client ready!"
    else:
        return "⚠️ Nija Bot is LIVE but Coinbase client FAILED!"

# -------- Webhook route --------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json() or {}
    secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")

    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 401

    print("✅ Webhook received:", data)

    if not COINBASE_OK:
        return jsonify({"error": "Coinbase client not available"}), 500

    # Example: process a trade
    try:
        action = data.get("action")  # "buy" or "sell"
        symbol = data.get("symbol")  # "BTC-USD" etc.
        size = float(data.get("size", 0.001))  # size of crypto to trade

        if action not in ["buy", "sell"]:
            return jsonify({"error": "invalid action"}), 400

        print(f"📝 Executing {action} order: {size} {symbol}")
        # Execute order on Coinbase
        order = COINBASE.create_order(
            product_id=symbol,
            side=action,
            type="market",
            size=str(size)
        )
        print("✅ Order executed:", order)
        return jsonify({"status": "success", "order": order})
    except Exception as e:
        print("❌ Error executing order:", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# -------- Run Flask --------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
