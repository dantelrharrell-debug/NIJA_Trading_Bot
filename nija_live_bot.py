import os
import json
import hmac
import hashlib
import time
from flask import Flask, request
import coinbase_advanced_py as cb

# === CONFIG ===
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")  # TradingView webhook secret

MIN_POSITION = 0.02  # 2% of equity
MAX_POSITION = 0.10  # 10% of equity

# === CONNECT TO COINBASE ===
if not API_KEY or not API_SECRET:
    raise ValueError("Missing Coinbase API key or secret!")

client = cb.Client(API_KEY, API_SECRET)
print("✅ Connected to Coinbase!")

# === FLASK APP TO RECEIVE TRADINGVIEW SIGNALS ===
app = Flask(__name__)

def calculate_position_size(balance, risk_percent):
    return round(balance * risk_percent, 2)

def execute_trade(symbol, side, size):
    try:
        order = client.create_order(
            product_id=symbol,
            side=side,
            type="market",
            size=str(size)
        )
        print(f"✅ Trade executed: {side.upper()} {size} {symbol}")
        return order
    except Exception as e:
        print(f"❌ Trade failed: {e}")
        return None

def verify_signature(payload, signature):
    computed = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, signature)

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    signature = request.headers.get("X-Signature", "")

    if not verify_signature(payload, signature):
        return "❌ Invalid signature", 403

    data = json.loads(payload)
    symbol = data.get("symbol", "BTC-USD")
    signal = data.get("signal", "").lower()  # "buy" or "sell"

    if signal not in ["buy", "sell"]:
        return "❌ Invalid signal", 400

    # Get USD balance
    accounts = client.get_accounts()
    balance = next((float(a.balance) for a in accounts if a.currency == "USD"), 0)
    position_size = calculate_position_size(balance, MAX_POSITION)

    print(f"⚡ Signal received: {signal.upper()} | Position size: ${position_size}")
    execute_trade(symbol, signal, position_size)

    return "✅ Trade executed", 200

if __name__ == "__main__":
    print("🚀 NIJA Bot is live and listening for TradingView signals...")
    app.run(host="0.0.0.0", port=5000)
