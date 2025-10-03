import os
import sys
import time
import json
from collections import deque

import numpy as np
from fastapi import FastAPI, Request
import uvicorn

# ======================
# Coinbase Advanced Import
# ======================
try:
    from coinbase_advanced_py import Client as CoinbaseClient
    print("✅ coinbase_advanced_py imported successfully")
except ModuleNotFoundError:
    import importlib.util
    spec = importlib.util.find_spec("coinbase_advanced_py")
    if spec is None:
        print("❌ coinbase_advanced_py NOT FOUND! Make sure it's in requirements.txt")
        sys.exit(1)
    else:
        from coinbase_advanced_py import Client as CoinbaseClient
        print("✅ coinbase_advanced_py imported via fallback")

# ======================
# CONFIG
# ======================
API_KEY = os.getenv("API_KEY") or "your_api_key_here"
API_SECRET = os.getenv("API_SECRET") or "your_api_secret_here"
SANDBOX = False  # True = test, False = live

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
    client = CoinbaseClient(api_key=API_KEY, api_secret=API_SECRET, sandbox=SANDBOX)
    print("✅ Connected to Coinbase Advanced")
except Exception as e:
    print("❌ Failed to connect:", e)
    sys.exit(1)

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
    coins = TRADE_COINS
    for coin in coins:
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
    base_confidence = max(0, min(1, base_confidence))

    symbol_data = learning_data.get(symbol, {})
    signal_type = f"MA_{int(short_ma*100)}"
    if signal_type in symbol_data and symbol_data[signal_type]["trades"] > 0:
        win_rate = symbol_data[signal_type]["wins"] / symbol_data[signal_type]["trades"]
        adjusted_conf = 0.5 * base_confidence + 0.5 * win_rate
        return adjusted_conf
    return base_confidence

def update_learning(symbol, pnl):
    symbol_data = learning_data.setdefault(symbol, {})
    signal_type = f"MA_{int(np.mean(list(price_history[symbol])[-5:])*100)}"
    signal_record = symbol_data.setdefault(signal_type, {"wins": 0, "trades": 0})
    signal_record["trades"] += 1
    if pnl > 0:
        signal_record["wins"] += 1
    learning_data[symbol] = symbol_data
    save_learning()

def volatility_adjusted_targets(symbol):
    price = get_price(symbol)
    volatility_factor = np.std(list(price_history[symbol])) / price if len(price_history[symbol]) > 1 else 0.02
    stop_loss = max(BASE_STOP_LOSS, volatility_factor)
    take_profit = max(BASE_TAKE_PROFIT, volatility_factor * 2)
    return stop_loss, take_profit

def check_stop_take(symbol, hedge=False):
    positions = hedge_positions if hedge else open_positions
    crypto = symbol.split("-")[0]
    if crypto not in positions:
        return
    price = get_price(symbol)
    stop_loss, take_profit = volatility_adjusted_targets(symbol)
    for pos in positions[crypto][:]:
        pnl_percent = (price - pos["price"]) / pos["price"]
        if pnl_percent <= -stop_loss:
            print(f"⚠ Stop-loss hit for {crypto} at ${price}")
            place_order(symbol, "sell", pos["amount_usd"], hedge=hedge)
            positions[crypto].remove(pos)
        elif pnl_percent >= take_profit:
            print(f"💰 Take-profit hit for {crypto} at ${price}")
            place_order(symbol, "sell", pos["amount_usd"], hedge=hedge)
            positions[crypto].remove(pos)

def adjust_trade_amount(default_amount, confidence):
    if len(trade_history) < 3:
        streak_factor = 1.0
    else:
        recent = trade_history[-3:]
        wins = sum(1 for t in recent if t["pnl"] > 0)
        streak_factor = 1.2 if wins >= 2 else 0.8
    amount = default_amount * streak_factor * confidence
    return max(1, min(amount, MAX_TRADE_AMOUNT))

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
        bought_usd = position["amount_usd"]
        bought_price = position["price"]
        pnl = (price - bought_price) / bought_price * bought_usd
        session_pnl += pnl
        update_learning(symbol, pnl)
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
    position_type = "HEDGE" if hedge else "MAIN"
    print(f"📌 Placing {position_type} {side.upper()} for ${amount_usd} of {symbol} at ${price}")

    try:
        order = client.place_order(
            product_id=symbol,
            side=side,
            order_type="market",
            funds=str(amount_usd)
        )
        pnl = calculate_pnl(symbol, side, amount_usd, price, hedge=hedge)
        trade_history.append({
            "symbol": symbol,
            "action": side.lower(),
            "amount": amount_usd,
            "price": price,
            "pnl": pnl,
            "hedge": hedge
        })
        if len(trade_history) > TRADE_HISTORY_LIMIT:
            trade_history.pop(0)
        print(f"✅ Order executed. PnL: {pnl:.2f}, Session PnL: {session_pnl:.2f}")
        return order
    except Exception as e:
        print(f"❌ Order failed: {e}")
        return None

def hedge_trade(symbol, amount_usd, main_action):
    correlation_matrix = compute_correlation_matrix()
    coins = TRADE_COINS
    idx = coins.index(symbol) if symbol in coins else 0
    correlations = correlation_matrix[idx]
    min_corr_idx = np.argmin(correlations)
    hedge_coin = coins[min_corr_idx] if not FUTURES_AVAILABLE else symbol
    hedge_side = "sell" if main_action.lower() == "buy" else "buy"
    print(f"⚡ Opening AI hedge for {hedge_coin}")
    return place_order(hedge_coin, hedge_side, amount_usd, hedge=True)

# ======================
# WEBHOOK ENDPOINT
# ======================
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("⚡ Webhook received:", data)

    action = data.get("action")
    symbol = data.get("symbol", "BTC-USD")
    amount = float(data.get("amount", DEFAULT_TRADE_AMOUNT))

    confidence = predictive_signal(symbol)
    amount = adjust_trade_amount(amount, confidence)

    for coin in TRADE_COINS:
        check_stop_take(coin)
        check_stop_take(coin, hedge=True)

    if action.lower() not in ["buy", "sell"]:
        return {"status": "error", "message": "Invalid action"}

    main_order = place_order(symbol, action.lower(), amount)
    hedge_order = hedge_trade(symbol, amount, action)

    return {
        "status": "success",
        "main_order": f"{action.upper()} executed for {symbol}",
        "hedge_order": f"Hedge executed for {symbol}",
        "confidence": confidence
    }

# ======================
# RUN BOT
# ======================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
