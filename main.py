from fastapi import FastAPI, Request
import uvicorn
import coinbase_advanced_py as cb
import os
import time

# ======================
# CONFIG
# ======================
API_KEY = "f0e7ae67-cf8a-4aee-b3cd-17227a1b8267"
API_SECRET = "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49"
SANDBOX = False  # True = test, False = live

DEFAULT_TRADE_AMOUNT = 10  # USD per trade
MAX_TRADE_AMOUNT = 100
MIN_USD_BALANCE = 5

TRADE_HISTORY_LIMIT = 50
STOP_LOSS_PERCENT = 0.05  # 5% loss
TAKE_PROFIT_PERCENT = 0.10  # 10% gain

FUTURES_AVAILABLE = True  # If Coinbase Futures account is accessible

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
# TRADE HISTORY & POSITIONS
# ======================
trade_history = []
open_positions = {}  # {coin: [positions]}
hedge_positions = {}  # {coin: [hedges]}
session_pnl = 0.0

# ======================
# HELPERS
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
        return float(ticker['price'])
    except Exception as e:
        print(f"❌ Error fetching price for {symbol}:", e)
        return 0.0

def calculate_pnl(symbol, action, amount_usd, price, hedge=False):
    """Calculate PnL and update session."""
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

def check_stop_take(symbol, hedge=False):
    positions = hedge_positions if hedge else open_positions
    crypto = symbol.split("-")[0]
    if crypto not in positions:
        return
    price = get_price(symbol)
    for pos in positions[crypto][:]:
        pnl_percent = (price - pos["price"]) / pos["price"]
        if pnl_percent <= -STOP_LOSS_PERCENT:
            print(f"⚠ Stop-loss hit for {crypto} at ${price}")
            place_order(symbol, "sell", pos["amount_usd"], hedge=hedge)
            positions[crypto].remove(pos)
        elif pnl_percent >= TAKE_PROFIT_PERCENT:
            print(f"💰 Take-profit hit for {crypto} at ${price}")
            place_order(symbol, "sell", pos["amount_usd"], hedge=hedge)
            positions[crypto].remove(pos)

def adjust_trade_amount(default_amount):
    if len(trade_history) < 3:
        return default_amount
    recent = trade_history[-3:]
    wins = sum(1 for t in recent if t["pnl"] > 0)
    if wins >= 2:
        return min(default_amount * 1.1, MAX_TRADE_AMOUNT)
    else:
        return max(default_amount * 0.9, 1)

def place_order(symbol, side, amount_usd, hedge=False):
    if amount_usd > MAX_TRADE_AMOUNT:
        amount_usd = MAX_TRADE_AMOUNT

    usd_balance = get_usd_balance()
    crypto_balance = get_crypto_balance(symbol)

    if side.lower() == "buy" and usd_balance < MIN_USD_BALANCE:
        print(f"⚠ USD balance too low (${usd_balance}). Trade skipped")
        return None

    if side.lower() == "sell" and crypto_balance <= 0:
        print(f"⚠ No crypto to sell ({symbol}). Trade skipped")
        return
