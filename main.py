# ======================
# MAIN.PY - Simplified for Render
# ======================

import os
import json
import time
from collections import deque

import numpy as np
from fastapi import FastAPI, Request
import uvicorn

# ======================
# Coinbase Advanced Import
# ======================
try:
    # Primary import
    from coinbase_advanced_py import Client as CoinbaseClient
    print("✅ coinbase_advanced_py imported successfully")
except ModuleNotFoundError:
    # Fallback check
    import importlib.util
    spec = importlib.util.find_spec("coinbase_advanced_py")
    if spec is None:
        print("❌ coinbase_advanced_py NOT FOUND! Make sure it's in requirements.txt")
        import sys
        sys.exit(1)
    else:
        from coinbase_advanced_py import Client as CoinbaseClient
        print("✅ coinbase_advanced_py imported via fallback")

# ======================
# Connect to Coinbase Advanced
# ======================
API_KEY = os.getenv("API_KEY") or "your_api_key_here"
API_SECRET = os.getenv("API_SECRET") or "your_api_secret_here"
SANDBOX = False  # True for test, False for live

try:
    client = CoinbaseClient(api_key=API_KEY, api_secret=API_SECRET, sandbox=SANDBOX)
    print("✅ Connected to Coinbase Advanced")
except Exception as e:
    print("❌ Failed to connect to Coinbase Advanced:", e)
    import sys
    sys.exit(1)

# ======================
# CONFIG
# ======================
API_KEY = os.getenv("API_KEY", "YOUR_API_KEY_HERE")
API_SECRET = os.getenv("API_SECRET", "YOUR_API_SECRET_HERE")
SANDBOX = os.getenv("SANDBOX", "False").lower() == "true"

DEFAULT_TRADE_AMOUNT = 10
MAX_TRADE_AMOUNT = 100
MIN_USD_BALANCE = 5
TRADE_HISTORY_LIMIT = 200
PRICE_HISTORY_LENGTH = 50

BASE_STOP_LOSS = 0.05
BASE_TAKE_PROFIT = 0.10
FUTURES_AVAILABLE = True

TRADE_COINS = ["BTC-USD", "ETH-USD", "LTC-USD", "SOL-USD"]
LEARNING_FILE = "trade_learning.json"

# ======================
# CONNECT TO COINBASE
# ======================
try:
    client = cb.CoinbaseAdvanced(api_key=API_KEY, api_secret=API_SECRET, sandbox=SANDBOX)
    print("✅ Connected to Coinbase Advanced")
except Exception as e:
    print("❌ Failed to connect:", e)
    exit(1)

# ======================
# FASTAPI SETUP
# ======================
app = FastAPI()

# ======================
# TRACKING STRUCTURES
# ======================
trade_history = []
open_positions = {}
hedge_positions = {}
session_pnl = 0.0
price_history = {coin: deque(maxlen=PRICE_HISTORY_LENGTH) for coin in TRADE_COINS}

# Load learning data
if os.path.exists(LEARNING_FILE):
    with open(LEARNING_FILE, "r") as f:
        learning_data = json.load(f)
else:
    learning_data = {}

# ======================
# HELPER FUNCTIONS
# ======================
def save_learning():
    with open(LEARNING_FILE, "w") as f:
        json.dump(learning_data, f, indent=2)

def get_usd_balance():
    try:
        accounts = client.get_accounts()
        for acc in accounts:
            if acc['currency'] == "USD":
                return float(acc['balance'])
    except Exception as e:
        print("❌ Error fetching USD balance:", e)
    return 0.0

def get_crypto_balance(symbol):
    crypto = symbol.split("-")[0]
    try:
        accounts = client.get_accounts()
        for acc in accounts:
            if acc['currency'] == crypto:
                return float(acc['balance'])
    except Exception as e:
        print(f"❌ Error fetching balance for {symbol}:", e)
    return 0.0

def get_price(symbol):
    try:
        ticker = client.get_product_ticker(symbol)
        price = float(ticker['price'])
        price_history[symbol].append(price)
        return price
    except Exception as e:
        print(f"❌ Error fetching price for {symbol}:", e)
        return 0.0

# ======================
# AI / PREDICTIVE FUNCTIONS
# ======================
def compute_correlation_matrix():
    data = []
    for coin in TRADE_COINS:
        hist = list(price_history[coin])
        if len(hist) < 2:
            hist = [get_price(coin)] * 2
        data.append(hist[-PRICE_HISTORY_LENGTH:])
    return np.corrcoef(data)

def predictive_signal(symbol):
    prices = list(price_history[symbol])
    if len(prices) < 2:
        return 0.5
    short_ma = np.mean(prices[-5:])
    long_ma = np.mean(prices[-15:]) if len(prices) >= 15 else short_ma
    momentum = prices[-1] - prices[-2]
    base_confidence = 0.5 + 0.3 * np.sign(short_ma - long_ma) + 0.2 * np.sign(momentum)
    return max(0, min(1, base_confidence))

# ======================
# ORDER FUNCTIONS
# ======================
def calculate_pnl(symbol, action, amount_usd, price, hedge=False):
    global session_pnl
    positions = hedge_positions if hedge else open_positions
    crypto = symbol.split("-")[0]

    if action.lower() == "buy":
        if crypto not in positions:
            positions[crypto] = []
        positions[crypto].append({"amount_usd": amount_usd, "price": price})
        return 0.0
    elif action.lower() == "sell":
        if crypto not in positions or len(positions[crypto]) == 0:
            return 0.0
        position = positions[crypto].pop(0)
        pnl = (price - position["price"]) / position["price"] * position["amount_usd"]
        session_pnl += pnl
        return pnl
    return 0.0

def place_order(symbol, side, amount_usd, hedge=False):
    usd_balance = get_usd_balance()
    crypto_balance = get_crypto_balance(symbol)
    if side.lower() == "buy" and usd_balance < MIN_USD_BALANCE:
        print(f"⚠ USD balance too low (${usd_balance}). Trade skipped")
        return None
    if side.lower() == "sell" and crypto_balance <= 0:
        print(f"⚠ No crypto to sell ({symbol}). Trade skipped")
        return None
    price = get_price(symbol)
    try:
        order = client.place_order(
            product_id=symbol,
            side=side,
            order_type="market",
            funds=str(amount_usd)
        )
        pnl = calculate_pnl(symbol, side, amount_usd, price, hedge=hedge)
        trade_history.append({"symbol": symbol, "action": side, "amount": amount_usd, "price": price, "pnl": pnl})
        if len(trade_history) > TRADE_HISTORY_LIMIT:
            trade_history.pop(0)
        print(f"✅ {side.upper()} {symbol} executed, PnL: {pnl:.2f}")
        return order
    except Exception as e:
        print(f"❌ Order failed: {e}")
        return None

# ======================
# WEBHOOK
# ======================
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    action = data.get("action")
    symbol = data.get("symbol", "BTC-USD")
    amount = float(data.get("amount", DEFAULT_TRADE_AMOUNT))

    if action.lower() not in ["buy", "sell"]:
        return {"status": "error", "message": "Invalid action"}

    confidence = predictive_signal(symbol)
    amount = max(1, min(amount * confidence, MAX_TRADE_AMOUNT))
    place_order(symbol, action.lower(), amount)

    return {"status": "success", "symbol": symbol, "action": action.upper(), "amount": amount, "confidence": confidence}

# ======================
# RUN BOT
# ======================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
