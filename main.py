# main.py
import os
import time
import threading
from flask import Flask, render_template_string, jsonify, request
from coinbase_advanced_py.client import Client

# ==========================
# Nija Live Crypto Trading Bot with TradingView signals
# ==========================

# Load API keys from environment variables
API_KEY = os.environ.get("COINBASE_API_KEY")
API_SECRET = os.environ.get("COINBASE_API_SECRET")
API_PASSPHRASE = os.environ.get("COINBASE_API_PASSPHRASE")  # optional

# Connect to Coinbase Advanced Trade
client = Client(API_KEY, API_SECRET, api_version="2023-08-01")

# Risk settings
MAX_RISK_PER_TRADE = 10
MIN_RISK_PERCENT = 2
MAX_RISK_PERCENT = 10

# Trailing settings
BASE_TRAILING_STOP_LOSS = 0.1
BASE_TRAILING_TAKE_PROFIT = 0.2

# Tick pairs to trade (add your symbols)
TICKERS = ["BTC-USD", "ETH-USD"]  # fill in later

# Dashboard data
dashboard_data = {
    "account_balance": 0,
    "last_trade": None,
    "last_signal": None,
    "trailing_stop": 0,
    "trailing_take_profit": 0,
    "heartbeat": "Offline"
}

# --------------------------
# Account & risk functions
def get_account_balance():
    accounts = client.get_accounts()
    for acc in accounts.data:
        if acc['currency'] == 'USD':
            return float(acc['available'])
    return 0.0

def calculate_risk(balance):
    min_risk = balance * (MIN_RISK_PERCENT / 100)
    max_risk = balance * (MAX_RISK_PERCENT / 100)
    return max(min_risk, min(max_risk, MAX_RISK_PER_TRADE))

def calculate_position(entry_price, stop_distance, balance):
    if stop_distance <= 0:
        stop_distance = 0.01
    risk_amount = calculate_risk(balance)
    size = risk_amount / stop_distance
    return size, risk_amount

def calculate_trailing(entry_price):
    tsl = entry_price * (1 - BASE_TRAILING_STOP_LOSS)
    ttp = entry_price * (1 + BASE_TRAILING_TAKE_PROFIT)
    return tsl, ttp

# --------------------------
# Trade execution
def open_trade(symbol, side, price, stop_distance):
    balance = get_account_balance()
    size, risk = calculate_position(price, stop_distance, balance)
    tsl, ttp = calculate_trailing(price)

    try:
        order = client.create_order(
            product_id=symbol,
            side=side.lower(),
            order_type="market",
            size=str(size)
        )

        dashboard_data.update({
            "account_balance": balance,
            "last_trade": f"{side} {symbol} @ ${price:.2f} ({size:.4f} units, Risk ${risk:.2f})",
            "last_signal": side,
            "trailing_stop": tsl,
            "trailing_take_profit": ttp,
            "heartbeat": "Online ✅"
        })

        print(f"[{side} TRADE] {symbol} Entry: ${price:.2f}, Size: {size:.4f}, Risk: ${risk:.2f}")
        print(f"TSL: ${tsl:.2f}, TTP: ${ttp:.2f}, Balance: ${balance:.2f}\n")

    except Exception as e:
        print(f"[ERROR] Failed to place order: {e}")

# --------------------------
# Flask + TradingView webhook endpoint
app = Flask(__name__)

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Nija Trading Bot Dashboard</title>
    <style>
        body { font-family: Arial; background-color: #121212; color: #f5f5f5; padding: 20px; }
        h1 { color: #00ff00; }
        .card { background: #1e1e1e; padding: 15px; margin: 10px 0; border-radius: 8px; }
    </style>
    <meta http-equiv="refresh" content="5">
</head>
<body>
    <h1>Nija Trading Bot Dashboard</h1>
    <div class="card"><strong>Status:</strong> {{ heartbeat }}</div>
    <div class="card"><strong>Account Balance:</strong> ${{ account_balance }}</div>
    <div class="card"><strong>Last Signal:</strong> {{ last_signal }}</div>
    <div class="card"><strong>Last Trade:</strong> {{ last_trade }}</div>
    <div class="card"><strong>Trailing Stop Loss:</strong> ${{ trailing_stop }}</div>
    <div class="card"><strong>Trailing Take Profit:</strong> ${{ trailing_take_profit }}</div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML, **dashboard_data)

@app.route("/heartbeat")
def heartbeat():
    return jsonify({"status": "alive"})

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    symbol = data.get("ticker")
    side = data.get("action")
    price = float(data.get("price", 0))
    stop_distance = price * 0.02

    if symbol in TICKERS and side in ["BUY", "SELL"]:
        open_trade(symbol, side, price, stop_distance)
        return jsonify({"status": "trade executed"}), 200
    return jsonify({"status": "ignored"}), 200

# --------------------------
# Persistent heartbeat logger
def heartbeat_loop():
    while True:
        dashboard_data["heartbeat"] = "Online ✅"
        time.sleep(5)

threading.Thread(target=heartbeat_loop, daemon=True).start()

# --------------------------
# Start Flask server
if __name__ == "__main__":
    print("Nija Trading Bot is live ✅")
    app.run(host="0.0.0.0", port=8080)
