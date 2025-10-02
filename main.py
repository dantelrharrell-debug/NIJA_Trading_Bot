from fastapi import FastAPI, Request
import uvicorn
import coinbase_advanced_py as cb
import os
import time
import numpy as np
from collections import deque

# ======================
# CONFIG
# ======================
API_KEY = "f0e7ae67-cf8a-4aee-b3cd-17227a1b8267"
API_SECRET = "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49"
SANDBOX = False  # True = test, False = live

DEFAULT_TRADE_AMOUNT = 10
MAX_TRADE_AMOUNT = 100
MIN_USD_BALANCE = 5
TRADE_HISTORY_LIMIT = 100

BASE_STOP_LOSS = 0.05
BASE_TAKE_PROFIT = 0.10
FUTURES_AVAILABLE = True  # For shorting/downside profit

TRADE_COINS = ["BTC-USD", "ETH-USD", "LTC-USD", "SOL-USD"]
PRICE_HISTORY_LENGTH = 50  # for correlation & predictive calculations

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
open_positions = {}       # {coin: [positions]}
hedge_positions = {}      # {coin: [hedges]}
session_pnl = 0.0

price_history = {coin: deque(maxlen=PRICE_HISTORY_LENGTH) for coin in TRADE_COINS}

# ======================
# HELPER FUNCTIONS
# ======================
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
    """Compute rolling correlations between coins."""
    data = []
    coins = TRADE_COINS
    for coin in coins:
        hist = list(price_history[coin])
        if len(hist) < 2:
            hist = [get_price(coin)] * 2
        data.append(hist[-PRICE_HISTORY_LENGTH:])
    return np.corrcoef(data)

def predictive_signal(symbol):
    """Generate a confidence score for a trade (0-1)."""
    prices = list(price_history[symbol])
    if len(prices) < 2:
        return 0.5
    short_ma = np.mean(prices[-5:])
    long_ma = np.mean(prices[-15:])
    momentum = prices[-1] - prices[-2]
    confidence = 0.5 + 0.3 * np.sign(short_ma - long_ma) + 0.2 * np.sign(momentum)
    confidence = max(0, min(1, confidence))
    return confidence

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
        return pnl
    return 0.0

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
        elif
