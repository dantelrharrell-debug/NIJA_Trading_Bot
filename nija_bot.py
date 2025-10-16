#!/usr/bin/env python3
import os
import time
import traceback
from flask import Flask, request, jsonify
from coinbase_advanced_py import CoinbaseAdvanced
import pandas as pd
import numpy as np

from dotenv import load_dotenv
load_dotenv()

# -------------------
# Settings
# -------------------
USE_MOCK = os.getenv("USE_MOCK", "False").lower() == "true"
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM_B64 = os.getenv("API_PEM_B64")
WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

# -------------------
# Initialize client
# -------------------
try:
    client = CoinbaseAdvanced(api_key=API_KEY, api_secret=API_SECRET, api_pem_b64=API_PEM_B64)
    print("✅ Coinbase client initialized. LIVE mode ON.")
except Exception as e:
    print("❌ Coinbase client failed:", e)
    USE_MOCK = True
    print("⚠️ Running in MOCK mode. No live trades will be executed.")

# -------------------
# Flask app
# -------------------
app = Flask(__name__)

# -------------------
# Indicators
# -------------------
def get_vwap(prices, volumes):
    return (prices * volumes).sum() / volumes.sum()

def get_rsi(prices, period=14):
    delta = prices.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(period).mean()
    avg_loss = pd.Series(loss).rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def get_ema(prices, period=21):
    return prices.ewm(span=period, adjust=False).mean().iloc[-1]

# -------------------
# Nija trade signal
# -------------------
def nija_trade_signal():
    data = client.get_candles("BTC-USD", granularity=60, limit=50)
    df = pd.DataFrame(data)
    
    price_now = df['close'].iloc[-1]
    df['vwap'] = get_vwap(df['close'], df['volume'])
    df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
    rsi = get_rsi(df['close'])

    trend_up = price_now > df['ema21'].iloc[-1]
    trend_down = price_now < df['ema21'].iloc[-1]

    # Aggressive logic: only follow trend + RSI + VWAP
    side = None
    if trend_up and price_now > df['vwap'].iloc[-1] and rsi < 70:
        side = "buy"
    elif trend_down and price_now < df['vwap'].iloc[-1] and rsi > 30:
        side = "sell"

    # Dynamic sizing: 2%-10% of equity based on volatility
    account = client.get_account("BTC-USD")
    balance = float(account['balance'])
    volatility = df['close'].pct_change().std() * 100
    risk_percent = max(2, min(10, 10 - volatility))  # lower size if volatile
    size = round(balance * (risk_percent/100), 8)

    if side:
        return {"side": side, "size": size, "price": price_now, "stop_loss": 0.995 if side=="buy" else 1.005, "take_profit": 1.01 if side=="buy" else 0.99}
    return None

# -------------------
# Webhook endpoint
# -------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")
    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 401

    try:
        trade = nija_trade_signal()
        if trade:
            if USE_MOCK:
                print("MOCK TRADE:", trade)
                return jsonify({"status": "mock trade executed", "trade": trade})
            order = client.place_order(
                symbol="BTC-USD",
                side=trade["side"],
                type="market",
                size=trade["size"]
            )
            print("LIVE TRADE EXECUTED:", order)
            return jsonify({"status": "live trade executed", "order": order})
        return jsonify({"status": "no trade signal"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# -------------------
# Health check
# -------------------
@app.route("/", methods=["GET", "HEAD"])
def index():
    return jsonify({"status": "Nija bot live"}), 200

# -------------------
# Run Flask
# -------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
