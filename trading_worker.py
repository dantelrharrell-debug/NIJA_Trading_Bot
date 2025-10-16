#!/usr/bin/env python3
# trading_worker.py

import os
import sys
import time
import threading
import traceback
import pkgutil
from dotenv import load_dotenv

load_dotenv()

# -------------------
# --- Dynamic Coinbase import & inspection guard ---
# -------------------
print("=== Coinbase import & inspection guard ===")
print("Python executable:", sys.executable)
print("cwd:", os.getcwd())
print("sys.path[:6]:", sys.path[:6])

CoinbaseAdvanced = None

_try_patterns = [
    ("coinbase_advanced_py", "CoinbaseAdvanced"),
    ("coinbase_advanced", "CoinbaseAdvanced"),
    ("coinbase", "CoinbaseAdvanced"),
    ("coinbase", "CoinbaseAdvancedClient"),
    ("coinbase", "CoinbaseClient"),
    ("coinbase", "Client"),
    ("coinbase", "Coinbase"),
    ("coinbase", "AdvancedClient"),
    ("coinbase", "CoinbasePro"),
    ("coinbase", "CoinbaseAPI"),
]

for mod_name, attr in _try_patterns:
    try:
        mod = __import__(mod_name)
        cand = getattr(mod, attr, None)
        if cand:
            CoinbaseAdvanced = cand
            print(f"FOUND: {attr} on module '{mod_name}'")
            break
        try:
            sub = __import__(f"{mod_name}.{attr}", fromlist=[attr])
            if sub:
                CoinbaseAdvanced = getattr(sub, attr, None)
                if CoinbaseAdvanced:
                    print(f"FOUND: {attr} in submodule {mod_name}.{attr}")
                    break
        except Exception:
            pass
    except Exception:
        pass

if CoinbaseAdvanced is None:
    print("ERROR: Could not import CoinbaseAdvanced client. Installed packages:")
    for p in pkgutil.iter_modules():
        name = p.name.lower()
        if any(k in name for k in ("coin", "base", "advanced")):
            print(" -", p.name)
    raise ImportError("coinbase client import failed (see logs).")

print("INFO: Coinbase client resolved:", CoinbaseAdvanced)

# -------------------
# Live trading toggle
# -------------------
LIVE_TRADING = os.getenv("LIVE_TRADING", "0").lower() in ("1", "true")
if LIVE_TRADING:
    print("⚠ LIVE_TRADING ENABLED — orders will be executed")
else:
    print("INFO: LIVE_TRADING disabled — simulation mode only")

# -------------------
# Initialize Coinbase client
# -------------------
client = CoinbaseAdvanced(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
    api_pem_b64=os.getenv("API_PEM_B64")
)

# -------------------
# --- Trading logic ---
# -------------------
def nija_trade_signal():
    """VWAP + RSI + EMA trend-based signal"""
    try:
        candles = client.get_historic_candles("BTC-USD", granularity=60, limit=50)
        prices = [float(c[4]) for c in candles]  # closing prices
        if len(prices) < 20:
            print("⚠ Not enough candles for analysis")
            return None

        vwap = sum(prices) / len(prices)
        current_price = prices[-1]

        gains = [max(0, prices[i] - prices[i-1]) for i in range(1, len(prices))]
        losses = [max(0, prices[i-1] - prices[i]) for i in range(1, len(prices))]
        avg_gain = sum(gains[-14:])/14
        avg_loss = sum(losses[-14:])/14
        rsi = 100 - (100 / (1 + avg_gain/avg_loss)) if avg_loss != 0 else 100

        ema = sum(prices[-20:])/20

        side = None
        if current_price > vwap and rsi < 70 and current_price > ema:
            side = "buy"
        elif current_price < vwap and rsi > 30 and current_price < ema:
            side = "sell"
        else:
            return None

        account = client.get_account("USD")
        equity = float(account['balance'])
        size_pct = 0.05  # 5% of equity
        size = (equity * size_pct) / current_price

        return {"side": side, "size": round(size, 6), "trail_pct": 0.005}

    except Exception as e:
        print("⚠ Trade signal error:", e)
        traceback.print_exc()
        return None

# -------------------
# Execute trade
# -------------------
def execute_trade():
    trade = nija_trade_signal()
    if trade:
        if LIVE_TRADING:
            try:
                order = client.place_order(
                    symbol="BTC-USD",
                    side=trade["side"],
                    type="market",
                    size=trade["size"],
                    trailing_stop_pct=trade["trail_pct"]
                )
                print("🚀 LIVE TRADE EXECUTED:", order)
            except Exception as e:
                print("⚠ Order placement failed:", e)
        else:
            print("⏸ Simulation: would execute trade:", trade)
    else:
        print("⏸ No trade signal currently.")

# -------------------
# Trailing stop monitor
# -------------------
def trailing_stop_monitor():
    while True:
        try:
            open_orders = client.get_open_orders("BTC-USD")
            ticker = client.get_ticker("BTC-USD")
            current_price = float(ticker['price'])

            for order in open_orders:
                side = order['side']
                stop_price = float(order.get('stop_price', 0))
                trail_pct = float(order.get('trailing_stop_pct', 0.005))

                if side == "buy":
                    new_stop = max(stop_price, current_price * (1 - trail_pct))
                    if new_stop > stop_price:
                        client.modify_order(order_id=order['id'], stop_price=new_stop)
                        print(f"⬆ BUY trailing stop updated: {new_stop:.2f}")
                elif side == "sell":
                    new_stop = min(stop_price, current_price * (1 + trail_pct))
                    if new_stop < stop_price or stop_price == 0:
                        client.modify_order(order_id=order['id'], stop_price=new_stop)
                        print(f"⬇ SELL trailing stop updated: {new_stop:.2f}")

        except Exception as e:
            print("⚠ Trailing stop monitor error:", e)
        time.sleep(5)

# -------------------
# Start background monitor
# -------------------
monitor_thread = threading.Thread(target=trailing_stop_monitor, daemon=True)
monitor_thread.start()
print("🚀 Trailing stop monitor running in background.")

# -------------------
# Main loop
# -------------------
if __name__ == "__main__":
    print("🚀 Trading worker started")
    while True:
        execute_trade()
        time.sleep(60)
