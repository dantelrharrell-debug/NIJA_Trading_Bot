# main.py
import os
import time
import asyncio
import json
from collections import deque
from typing import Optional

from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

# --- Resilient import for coinbase advanced ---
_coinbase_module = None
_import_name = None
_candidates = [
    "coinbase_advanced_py",
    "coinbase_advanced",
    "coinbase_advanced_py.client",
    "coinbase_advanced.client",
    "coinbase_advanced_py.core",
    "coinbase_advanced.core",
]
for name in _candidates:
    try:
        import importlib
        mod = importlib.import_module(name)
        _coinbase_module = mod
        _import_name = name
        break
    except Exception:
        continue

if _coinbase_module is None:
    # If not found, show clear message and exit so logs show this error.
    print("❌ ERROR: Could not import any Coinbase Advanced module. Tried:", _candidates)
    print("Make sure 'coinbase-advanced-py' is in requirements.txt and installed.")
    raise SystemExit(1)

# Use the module as `cb`
cb = _coinbase_module

# ========== CONFIG ==========
API_KEY = os.getenv("API_KEY", "")
API_SECRET = os.getenv("API_SECRET", "")
SANDBOX = os.getenv("SANDBOX", "true").lower() in ("1", "true", "yes")

TRADE_INTERVAL_SECONDS = int(os.getenv("TRADE_INTERVAL_SECONDS", "180"))  # 3 minutes default
MIN_USD_BALANCE = float(os.getenv("MIN_USD_BALANCE", "5"))
DEFAULT_TRADE_AMOUNT = float(os.getenv("DEFAULT_TRADE_AMOUNT", "10"))
MAX_TRADE_AMOUNT = float(os.getenv("MAX_TRADE_AMOUNT", "100"))
PRICE_HISTORY_LENGTH = int(os.getenv("PRICE_HISTORY_LENGTH", "50"))

TRADE_COINS = os.getenv("TRADE_COINS", "BTC-USD,ETH-USD").split(",")
LEARNING_FILE = "trade_learning.json"

# ========== CONNECT CLIENT ==========
client = None
try:
    # try common client factories
    if hasattr(cb, "Client"):
        # many wrappers expose Client(...) or similar
        try:
            client = cb.Client(api_key=API_KEY, api_secret=API_SECRET, sandbox=SANDBOX)
        except TypeError:
            # alternative signature
            client = cb.Client(API_KEY, API_SECRET, SANDBOX)
    elif hasattr(cb, "CoinbaseAdvanced"):
        client = cb.CoinbaseAdvanced(api_key=API_KEY, api_secret=API_SECRET, sandbox=SANDBOX)
    else:
        # fallback: use the module directly (maybe it acts as client factory)
        client = cb
    print(f"✅ Imported Coinbase module from '{_import_name}' and initialized client (sandbox={SANDBOX})")
except Exception as e:
    print("❌ Failed to initialize Coinbase client:", e)
    client = None

# ========== STATE ==========
app = FastAPI(title="NIJA Trading Bot")
trade_history = []
open_positions = {}
hedge_positions = {}
session_pnl = 0.0
price_history = {coin: deque(maxlen=PRICE_HISTORY_LENGTH) for coin in TRADE_COINS}
learning_data = {}
_trading_task: Optional[asyncio.Task] = None
_trading_paused = False

# load learning data if exists
if os.path.exists(LEARNING_FILE):
    try:
        with open(LEARNING_FILE, "r") as f:
            learning_data = json.load(f)
    except Exception:
        learning_data = {}

def save_learning():
    try:
        with open(LEARNING_FILE, "w") as f:
            json.dump(learning_data, f, indent=2)
    except Exception as e:
        print("Error saving learning file:", e)

# ========== UTILITIES ==========
def safe_get_usd_balance():
    if client is None:
        return 0.0
    try:
        # best-effort: many wrappers expose get_accounts or get_account_balance methods
        if hasattr(client, "get_accounts"):
            accounts = client.get_accounts()
            for acc in accounts:
                if str(acc.get("currency", "")).upper() == "USD":
                    return float(acc.get("balance", 0.0))
        elif hasattr(client, "get_balance"):
            return float(client.get_balance("USD"))
    except Exception as e:
        print("Error fetching USD balance:", e)
    return 0.0

def safe_get_price(symbol):
    # wrapper may expose get_product_ticker or get_price
    if client is None:
        return 0.0
    try:
        if hasattr(client, "get_product_ticker"):
            ticker = client.get_product_ticker(symbol)
            price = float(ticker.get("price") if isinstance(ticker, dict) else ticker)
            price_history[symbol].append(price)
            return price
        elif hasattr(client, "get_price"):
            p = client.get_price(symbol)
            price_history[symbol].append(float(p))
            return float(p)
    except Exception as e:
        print(f"Error fetching price for {symbol}:", e)
    return 0.0

def predictive_signal(symbol):
    # simple MA crossover + momentum heuristic (0..1)
    pr = list(price_history.get(symbol, []))
    if len(pr) < 2:
        return 0.5
    short = sum(pr[-5:]) / min(len(pr[-5:]), 5)
    long = sum(pr[-15:]) / min(len(pr[-15:]), 15)
    momentum = pr[-1] - pr[-2]
    score = 0.5 + 0.25 * (1 if short > long else -1) + 0.25 * (1 if momentum > 0 else -1)
    return max(0.0, min(1.0, score))

def adjust_trade_amount(confidence):
    base = DEFAULT_TRADE_AMOUNT * confidence
    return max(1, min(base, MAX_TRADE_AMOUNT))

async def place_order(symbol, side, amount_usd, hedge=False):
    """Place or simulate an order. Returns dict or None."""
    price = safe_get_price(symbol)
    if SANDBOX or client is None:
        # simulate
        print(f"[SIM] {side.upper()} ${amount_usd:.2f} of {symbol} at ${price:.2f}")
        # update simulated positions
        if side.lower() == "buy":
            open_positions.setdefault(symbol.split("-")[0], []).append({"amount_usd": amount_usd, "price": price})
            return {"status": "simulated", "symbol": symbol, "side": side, "price": price}
        else:
            # sell: pop oldest
            crypto = symbol.split("-")[0]
            if crypto in open_positions and open_positions[crypto]:
                pos = open_positions[crypto].pop(0)
                pnl = (price - pos["price"]) / pos["price"] * pos["amount_usd"]
                return {"status": "simulated", "pnl": pnl}
            return {"status": "simulated", "message": "no position"}
    else:
        try:
            # best-effort: call place_order if available
            if hasattr(client, "place_order"):
                order = client.place_order(product_id=symbol, side=side, order_type="market", funds=str(amount_usd))
                print("Order response:", order)
                return order
            else:
                print("No place_order on client; cannot execute live order.")
        except Exception as e:
            print("Live order failed:", e)
    return None

# ========== TRADING LOOP ==========
async def trading_loop():
    global _trading_paused
    print("🔁 Trading loop started. Interval:", TRADE_INTERVAL_SECONDS, "s. Sandbox:", SANDBOX)
    while True:
        if _trading_paused:
            await asyncio.sleep(1)
            continue

        usd_balance = safe_get_usd_balance()
        print("USD balance:", usd_balance)

        for symbol in TRADE_COINS:
            try:
                price = safe_get_price(symbol)
                if price <= 0:
                    continue
                confidence = predictive_signal(symbol)
                amount = adjust_trade_amount(confidence)
                if usd_balance < MIN_USD_BALANCE:
                    print(f"⚠ USD balance below minimum ({usd_balance} < {MIN_USD_BALANCE}) — skipping trades.")
                    break

                # Simple rule: buy if confidence > 0.6, sell if < 0.4 (simulated)
                if confidence > 0.6:
                    print(f"Signal BUY {symbol} conf={confidence:.2f}")
                    await place_order(symbol, "buy", amount)
                elif confidence < 0.4:
                    print(f"Signal SELL {symbol} conf={confidence:.2f}")
                    await place_order(symbol, "sell", amount)
                else:
                    print(f"{symbol}: no clear signal (conf={confidence:.2f})")
            except Exception as e:
                print("Error during trading for", symbol, e)

        await asyncio.sleep(TRADE_INTERVAL_SECONDS)

# ========== FASTAPI ENDPOINTS ==========
@app.on_event("startup")
async def startup_event():
    global _trading_task
    # ensure price history warm-up once
    for symbol in TRADE_COINS:
        try:
            p = safe_get_price(symbol)
            if p:
                print(f"Initial price for {symbol}: {p}")
        except Exception:
            pass
    if _trading_task is None:
        # spawn background loop
        _trading_task = asyncio.create_task(trading_loop())

@app.get("/")
def root():
    return {"status": "ok", "message": "NIJA Trading Bot live", "sandbox": SANDBOX}

@app.get("/check-coinbase")
def check_coinbase():
    if client is None:
        return {"status": "error", "message": "Client not initialized"}
    return {"status": "ok", "client_module": _import_name, "sandbox": SANDBOX}

@app.get("/balance")
def get_balance():
    b = safe_get_usd_balance()
    return {"usd_balance": b}

@app.post("/pause")
def pause_trading():
    global _trading_paused
    _trading_paused = True
    return {"status": "ok", "message": "Trading paused"}

@app.post("/resume")
def resume_trading():
    global _trading_paused
    _trading_paused = False
    return {"status": "ok", "message": "Trading resumed"}
