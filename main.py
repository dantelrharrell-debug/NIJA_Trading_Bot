#!/usr/bin/env python3
"""
NIJA Trading Bot - Render-friendly bootstrap
Ensures virtualenv packages load first and handles Coinbase API.
"""

import os
import sys

# -------------------------------------------------
# Ensure Render virtualenv packages are first in sys.path
# -------------------------------------------------
VENV_PATH = os.path.join(os.getcwd(), ".venv", "lib", "python3.13", "site-packages")
if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)

# -------------------------------------------------
# Load environment variables
# -------------------------------------------------
from dotenv import load_dotenv
load_dotenv()

# -------------------------------------------------
# Debug info to confirm virtualenv is being used
# -------------------------------------------------
print(f"Python executable: {sys.executable}")
print(f"sys.path:\n  " + "\n  ".join(sys.path))

# -------------------------------------------------
# Try to import coinbase_advanced_py
# -------------------------------------------------
USE_LIVE = True
try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py import OK")
except ImportError as e:
    print("❌ coinbase_advanced_py import failed:", e)
    USE_LIVE = False

# -------------------------------------------------
# Fallback MockClient
# -------------------------------------------------
if not USE_LIVE:
    class MockClient:
        def get_account_balances(self):
            return {"USD": 10000.0, "BTC": 0.05}

        def place_order(self, *args, **kwargs):
            raise RuntimeError("DRY RUN: MockClient refuses to place orders")

    client = MockClient()
    LIVE_TRADING = False
    print("⚠️ Using MockClient (no live trading)")
else:
    # Initialize real client
    PEM_B64 = os.getenv("API_PEM_B64")
    PEM_PATH = "/tmp/my_coinbase_key.pem"
    if PEM_B64:
        with open(PEM_PATH, "w") as f:
            f.write(PEM_B64)
        print(f"✅ PEM written to {PEM_PATH}")
    client = cb.CoinbaseAdvancedAPIClient(
        pem_path=PEM_PATH,
        api_key=os.getenv("API_KEY"),
        api_secret=os.getenv("API_SECRET"),
        passphrase=os.getenv("API_PASSPHRASE")
    )
    LIVE_TRADING = True
    print("🚀 Live Coinbase client initialized")

#!/usr/bin/env python3
# NIJA BOT - Self-Optimizing Smart Signal Engine
# Uses coinbase-advanced-py (import name: coinbase_advanced_py)

import os
import sys
import time
import json
import traceback
import importlib
from typing import List, Dict

# Use the installed coinbase library
try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    # Helpful error: runtime installer approach could be added if needed
    print("❌ coinbase_advanced_py not installed. Install coinbase-advanced-py==1.8.2")
    raise

# ---------------------------
# Configuration / env
# ---------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set")

# Initialize client
client = cb.Client(API_KEY, API_SECRET)
print("🚀 Coinbase client initialized successfully")

MIN_ALLOCATION = 0.02
MAX_ALLOCATION = 0.10
TRADE_SYMBOLS = ["BTC", "ETH"]          # short symbols; code converts to market (e.g. BTC-USD)
SLEEP_SECONDS = 60
BASE_COOLDOWN = 300
TRADE_LOG = "trades.jsonl"
TRADE_HISTORY_COUNT = 5

last_trade_time = {symbol: 0 for symbol in TRADE_SYMBOLS}

# ---------------------------
# Helpers
# ---------------------------
def market_for(symbol: str) -> str:
    """Convert short symbol to Coinbase product id (market)."""
    # Adjust if you trade other quote currencies
    return f"{symbol}-USD"

def safe_get_spot_price(market: str) -> float:
    """Try common methods to get a spot price (adapt to client API)."""
    # coinbase_advanced_py has get_price(product_id) in many wrappers
    try:
        # Try get_price first (returns dict with 'amount') if available
        price = client.get_price(market)
        if isinstance(price, dict) and "amount" in price:
            return float(price["amount"])
        # Some versions return plain float/str
        return float(price)
    except Exception:
        pass

    try:
        # fallback name used in earlier code
        price = client.get_spot_price(market)
        if isinstance(price, dict) and "amount" in price:
            return float(price["amount"])
        return float(price)
    except Exception:
        pass

    raise RuntimeError(f"Unable to fetch spot price for {market}")

def print_balances() -> List[Dict]:
    try:
        balances = client.get_account_balances()
        # Expecting a list of dicts with 'currency' and 'balance' keys; adapt if shape differs.
        for account in balances:
            try:
                cur = account.get("currency", account.get("currency_code", "UNK"))
                bal = account.get("balance", account.get("available", 0))
                print(f"💰 {cur}: {bal}")
            except Exception:
                pass
        return balances
    except Exception as e:
        print("❌ Error fetching balances:", e)
        traceback.print_exc()
        return []

def get_account_equity(balances: List[Dict]) -> float:
    total = 0.0
    try:
        for account in balances:
            cur = account.get("currency", account.get("currency_code"))
            bal = float(account.get("balance", account.get("available", 0)) or 0)
            if not cur:
                continue
            if cur.upper() in ("USD", "USDC", "USDT"):
                total += bal
            else:
                market = market_for(cur.upper())
                try:
                    price = safe_get_spot_price(market)
                    total += bal * price
                except Exception:
                    # If we can't price the asset, skip it
                    pass
    except Exception as e:
        print("❌ Error calculating equity:", e)
        traceback.print_exc()
    return total

def calculate_trade_amount(equity: float, allocation_percent: float, price: float) -> float:
    allocation_percent = max(MIN_ALLOCATION, min(MAX_ALLOCATION, allocation_percent))
    usd_amount = equity * allocation_percent
    if price <= 0:
        return 0.0
    amount = usd_amount / price
    # round to 8 decimals (adjust precision to asset)
    return round(amount, 8)

def get_historic_closes(market: str, period: int, granularity: int = 60) -> List[float]:
    """
    Wrapper to fetch historical candle data. Expects client.get_historic_rates(market, granularity)
    which returns list of candlesticks where index 4 is close and index 5 is volume (per your prior usage).
    """
    try:
        candles = client.get_historic_rates(market, granularity=granularity)
        closes = [float(c[4]) for c in candles]
        return closes[-period:]
    except Exception as e:
        print(f"❌ Error fetching historic rates for {market}:", e)
        return []

def get_rsi(symbol: str, period: int = 14) -> float:
    market = market_for(symbol)
    closes = get_historic_closes(market, period + 1)
    if len(closes) < period + 1:
        return 50.0
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_vwap(symbol: str, period: int = 20) -> float:
    market = market_for(symbol)
    try:
        candles = client.get_historic_rates(market, granularity=60)
        recent = candles[-period:]
        closes = [float(c[4]) for c in recent]
        volumes = [float(c[5]) for c in recent]
        vol_sum = sum(volumes)
        if vol_sum == 0:
            return safe_get_spot_price(market)
        return sum(c * v for c, v in zip(closes, volumes)) / vol_sum
    except Exception as e:
        print(f"❌ VWAP error for {symbol}:", e)
        return safe_get_spot_price(market)

def get_volatility(symbol: str, period: int = 20) -> float:
    market = market_for(symbol)
    closes = get_historic_closes(market, period)
    if not closes:
        return 0.0
    mean = sum(closes) / len(closes)
    variance = sum((p - mean) ** 2 for p in closes) / len(closes)
    return variance ** 0.5

def load_trade_history() -> Dict[str, List[Dict]]:
    history = {}
    if os.path.exists(TRADE_LOG):
        with open(TRADE_LOG, "r") as f:
            for line in f:
                try:
                    t = json.loads(line)
                    history.setdefault(t.get("symbol"), []).append(t)
                except Exception:
                    continue
    return history

def adjust_allocation(symbol: str, base_percent: float) -> float:
    history = load_trade_history().get(symbol, [])[-TRADE_HISTORY_COUNT:]
    if not history:
        return base_percent
    # average profit over recent trades (if profit field present)
    profits = [float(t.get("profit", 0) or 0) for t in history]
    profit_factor = sum(profits) / TRADE_HISTORY_COUNT
    allocation = base_percent + (profit_factor * 0.5)
    volatility = get_volatility(symbol)
    allocation = allocation / (1 + volatility)
    return max(MIN_ALLOCATION, min(MAX_ALLOCATION, allocation))

def can_trade(symbol: str) -> bool:
    return time.time() - last_trade_time.get(symbol, 0) > BASE_COOLDOWN

def place_trade(symbol: str, side: str, base_allocation: float = 0.05):
    try:
        balances = print_balances()
        equity = get_account_equity(balances)
        market = market_for(symbol)
        price = safe_get_spot_price(market)
        allocation = adjust_allocation(symbol, base_allocation)
        amount = calculate_trade_amount(equity, allocation, price)

        if amount <= 0:
            print(f"⚠️ Computed trade amount is zero for {symbol}, skipping")
            return

        if not can_trade(symbol):
            print(f"⏳ Cooldown active for {symbol}, skipping trade")
            return

        print(f"⚡ Placing {side.upper()} {symbol}: amount={amount} (~{allocation*100:.1f}% equity) at price {price}")

        # NOTE: coinbase_advanced_py client place_order signature may differ.
        # Example parameter names used by various clients:
        #   client.place_order(product_id=market, side=side, order_type="market", size=str(amount))
        # or
        #   client.place_order(symbol=market, side=side, type="market", amount=str(amount))
        #
        # Inspect your client's method signature and adjust below if needed.
        try:
            order = client.place_order(product_id=market, side=side, order_type="market", size=str(amount))
        except TypeError:
            # fallback to alternative param names
            order = client.place_order(symbol=market, side=side, type="market", amount=str(amount))
        except Exception as e:
            # final fallback: try a very generic call (if client implements differently, update code)
            print("⚠️ place_order attempt failed:", e)
            raise

        last_trade_time[symbol] = time.time()

        # Log trade (no PII)
        record = {
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "price": price,
            "timestamp": time.time()
        }
        with open(TRADE_LOG, "a") as f:
            f.write(json.dumps(record) + "\n")
        print("✅ Trade executed and logged:", record)

    except Exception as e:
        print("❌ Trade failed:", e)
        traceback.print_exc()

# ---------------------------
# Main loop
# ---------------------------
def main_loop():
    print("🌟 NIJA BOT Self-Optimizing Loop Starting")
    while True:
        try:
            balances = print_balances()
            equity = get_account_equity(balances)
            print(f"💵 Total Equity: ${equity:.2f}")

            for symbol in TRADE_SYMBOLS:
                rsi = get_rsi(symbol)
                vwap = get_vwap(symbol)
                market = market_for(symbol)
                try:
                    price = safe_get_spot_price(market)
                except Exception as e:
                    print(f"❌ Could not fetch price for {symbol}: {e}")
                    continue

                print(f"📊 {symbol} RSI:{rsi:.2f} Price:{price:.2f} VWAP:{vwap:.2f}")

                # simple signals
                if price < vwap and rsi < 30:
                    place_trade(symbol, "buy")
                elif price > vwap and rsi > 70:
                    place_trade(symbol, "sell")
                else:
                    print(f"ℹ️ No signal for {symbol}")

        except Exception as e:
            print("❌ Main loop error:", e)
            traceback.print_exc()

        print(f"⏳ Sleeping {SLEEP_SECONDS}s before next cycle\n")
        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    main_loop()
