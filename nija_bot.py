#!/usr/bin/env python3
import os
import json
from datetime import datetime
from flask import Flask, request, jsonify

# Coinbase client
try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    cb = None
    print("❌ coinbase_advanced_py not found. Running in mock mode.")

# ------------------ BOT SETTINGS ------------------
TICKERS = ["BTC", "ETH", "SOL", "ADA"]  # add your tickers
LIVE_TRADING = True

RISK = {"min_pct": 0.02, "max_pct": 0.10}
STATE = {"trade_history": []}

# ---------- Coinbase client ----------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET or cb is None:
    print("⚠️ Running in mock mode — Coinbase client not connected.")
    client = None
else:
    client = cb.Client(API_KEY, API_SECRET)

# ---------- Flask App ----------
app = Flask(__name__)

# ---------- AI Trade Logic ----------
def ai_trade_decision(ticker, price, indicators):
    rsi = indicators.get("rsi", 50)
    vwap = indicators.get("vwap", price)
    ema50 = indicators.get("ema50", price)

    if price > vwap and price > ema50 and rsi < 30:
        return "buy"
    elif price < vwap and price < ema50 and rsi > 70:
        return "sell"
    else:
        return "hold"

# ---------- Position Sizing ----------
def calculate_position_size(ticker, account_balance=1000):
    pct = RISK["min_pct"]
    size = account_balance * pct
    max_size = account_balance * RISK["max_pct"]
    if size > max_size:
        size = max_size
    return round(size, 6)

# ---------- Trade Handler ----------
def handle_trade_signal(ticker, action, price, indicators):
    if action == "auto":
        action = ai_trade_decision(ticker, price, indicators)

    if action == "hold":
        return {"status": "hold", "ticker": ticker, "price": price}

    trade_size = calculate_position_size(ticker)
    STATE["trade_history"].append({
        "time": str(datetime.utcnow()),
        "ticker": ticker,
        "action": action,
        "price": price,
        "size": trade_size
    })

    if LIVE_TRADING and client:
        try:
            # Spot trade
            client.place_order(symbol=f"{ticker}-USD", side=action, type="market", size=trade_size)
            # Futures trade
            client.place_order(symbol=f"{ticker}-USD", side=action, type="market", size=trade_size, futures=True)
            print(f"✅ {action.upper()} order placed for {ticker} at {price} (${trade_size})")
        except Exception as e:
            print("❌ Order failed:", e)
            return {"status": "error", "message": str(e)}

    return {"status": "success", "ticker": ticker, "action": action, "price": price, "size": trade_size}

# ---------- Webhook Endpoint ----------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    ticker = data.get("ticker")
    action = data.get("action", "auto")
    price = data.get("price")
    indicators = data.get("indicators", {})

    if ticker not in TICKERS:
        return jsonify({"error": "Ticker not tracked"}), 400

    result = handle_trade_signal(ticker, action, price, indicators)
    return jsonify(result)

# ---------- Health Check ----------
@app.route("/", methods=["GET", "HEAD"])
def home():
    return "NIJA BOT is alive!", 200

# ---------- Start Bot ----------
if __name__ == "__main__":
    print("🟢 NIJA BOT starting; LIVE_TRADING =", LIVE_TRADING)
    app.run(host="0.0.0.0", port=10000)
