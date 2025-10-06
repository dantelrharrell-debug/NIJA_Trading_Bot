import os
import json
from flask import Flask, request
from coinbase_advanced_py import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise ValueError("❌ Missing Coinbase API_KEY or API_SECRET")

# Initialize Coinbase client
client = Client(API_KEY, API_SECRET)
print("🚀 Coinbase Bot Initialized - Live Trading Active")

# Flask app to receive TradingView webhooks
app = Flask(__name__)

# Minimum order check
MIN_USD_ORDER = 10  # adjust according to Coinbase minimums

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("📡 Received TradingView signal:", data)

    try:
        # Extract trading info from TradingView alert
        symbol = data.get("symbol")  # e.g., BTC-USD
        side = data.get("side")      # 'buy' or 'sell'
        amount = float(data.get("amount", 0))  # USD amount to trade

        if amount < MIN_USD_ORDER:
            print(f"⚠️ Order below minimum (${MIN_USD_ORDER}), skipping.")
            return "Order too small", 400

        # Place live order on Coinbase
        order = client.place_order(
            product_id=symbol,
            side=side,
            order_type="market",
            funds=amount  # amount in USD
        )
        print("✅ Order placed:", order)
        return json.dumps({"status": "success", "order": order}), 200

    except Exception as e:
        print("❌ Error placing order:", e)
        return json.dumps({"status": "error", "message": str(e)}), 500

# Keep bot running 24/7
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
