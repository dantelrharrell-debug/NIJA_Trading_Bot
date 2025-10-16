# --- dynamic coinbase import + introspection guard ---
import os, sys, pkgutil, traceback

print("=== coinbase import & inspection guard ===")
print("Python executable:", sys.executable)
print("cwd:", os.getcwd())
print("sys.path[:6]:", sys.path[:6])

CoinbaseAdvanced = None
_client_candidates = [
    "CoinbaseAdvanced",
    "CoinbaseAdvancedClient",
    "CoinbaseClient",
    "Coinbase",
    "Client",
    "CoinbasePro",
    "CoinbaseAPI",
    "AdvancedClient",
]

# Try to import top-level names first
try:
    import coinbase as _coinbase_mod
    print("INFO: imported top-level package 'coinbase'")
except Exception as e:
    _coinbase_mod = None
    print("INFO: no top-level 'coinbase' package importable:", type(e).__name__, e)

# If coinbase loaded, list its attributes and submodules to logs for diagnosis
if _coinbase_mod is not None:
    try:
        attrs = sorted([a for a in dir(_coinbase_mod) if not a.startswith("_")])
        print("coinbase package attributes (top ~100):", attrs[:100])
    except Exception:
        traceback.print_exc()
    # list internal modules/files
    try:
        if hasattr(_coinbase_mod, "__path__"):
            print("coinbase __path__ (package contents):", list(_coinbase_mod.__path__))
            print("coinbase submodules / files:")
            for info in pkgutil.iter_modules(_coinbase_mod.__path__):
                print(" -", info.name)
    except Exception:
        traceback.print_exc()

# Try many import patterns (module, from module import name)
_try_patterns = [
    ("coinbase_advanced_py", "CoinbaseAdvanced"),
    ("coinbase_advanced", "CoinbaseAdvanced"),
    ("coinbase", "CoinbaseAdvanced"),        # original expectation
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
        # if attribute is on the module, use it
        cand = getattr(mod, attr, None)
        if cand:
            CoinbaseAdvanced = cand
            print(f"FOUND: {attr} on module '{mod_name}' — using that as client.")
            break
        # if module has submodule, try importlib.import_module('mod_name.attr')
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
        # ignore missing module
        pass

# If still not found, try scanning installed site-packages for related names (diagnostic)
if CoinbaseAdvanced is None:
    print("WARNING: Could not find an attribute matching expected client class names.")
    try:
        print("Installed site-packages entries (filtered):")
        for p in pkgutil.iter_modules():
            name = p.name
            if any(k in name.lower() for k in ("coin", "base", "advanced")):
                print(" -", name)
    except Exception:
        traceback.print_exc()
    # Print helpful message to logs and fail fast so Render/gunicorn shows logs
    raise ImportError(
        "coinbase client import failed: installed package present but no supported client class found. "
        "Check the package's exposed API; paste the 'coinbase package attributes' log above and I will map the correct import."
    )

print("INFO: coinbase client resolved to:", CoinbaseAdvanced)
# keep LIVE_TRADING toggle
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") in ("1", "true", "True")
if not LIVE_TRADING:
    print("INFO: LIVE_TRADING disabled — bot will simulate orders only.")
else:
    print("WARNING: LIVE_TRADING enabled — bot will place real orders.")

print("=== end coinbase import & inspection guard ===")

# === diagnostic import guard (temporary) ===
import sys, traceback, os
print("=== nija_bot.py import guard ===")
print("Python executable:", sys.executable)
print("cwd:", os.getcwd())
print("sys.path:", sys.path[:6])

_import_candidates = [
    ("coinbase_advanced_py", "from coinbase_advanced_py import CoinbaseAdvanced"),
    ("coinbase_advanced", "from coinbase_advanced import CoinbaseAdvanced"),
    ("coinbase", "from coinbase import CoinbaseAdvanced"),
]

CoinbaseAdvanced = None
for module_name, stmt in _import_candidates:
    try:
        __import__(module_name)
        print(f"INFO: module '{module_name}' import OK")
        try:
            exec(stmt, globals())
            print(f"INFO: executed: {stmt}")
            CoinbaseAdvanced = globals().get("CoinbaseAdvanced")
            break
        except Exception as e:
            print(f"WARNING: couldn't execute '{stmt}':", type(e).__name__, e)
    except Exception as e:
        print(f"INFO: module '{module_name}' import failed: {type(e).__name__}: {e}")

if CoinbaseAdvanced is None:
    print("ERROR: Could not import coinbase client under any tested name.")
    print("Installed site-packages snapshot:")
    try:
        import pkgutil
        for p in pkgutil.iter_modules():
            name = p.name.lower()
            if "coin" in name or "base" in name or "advanced" in name:
                print(" -", p.name)
    except Exception:
        traceback.print_exc()
    raise ImportError("coinbase client import failed (see logs).")
print("=== import guard finished ===")

# === your original imports start here ===
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
load_dotenv()
# ... rest of your code ...

import sys, os
print("Python executable:", sys.executable)
print("sys.path:", sys.path)
import coinbase_advanced_py
print("✅ coinbase_advanced_py is imported")

import os
import time
import threading
from coinbase_advanced_py import CoinbaseAdvanced

# -------------------
# Initialize Coinbase client
# -------------------
client = CoinbaseAdvanced(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET"),
    api_pem_b64=os.getenv("API_PEM_B64")
)

# -------------------
# Strategy: Nija Signal (VWAP + RSI + Trend)
# -------------------
def nija_trade_signal():
    """
    Determines the best trade side (buy/sell) and dynamic size
    based on VWAP, RSI, EMA trend logic.
    Returns dict: {'side': 'buy'/'sell', 'size': float, 'trail_pct': float}
    """
    # Fetch BTC ticker & historical candles
    candles = client.get_historic_candles("BTC-USD", granularity=60, limit=50)
    prices = [float(c[4]) for c in candles]  # closing prices

    # Simple VWAP calculation
    vwap = sum(prices) / len(prices)
    current_price = prices[-1]

    # Simple RSI calculation (14-period)
    gains = [max(0, prices[i] - prices[i-1]) for i in range(1, len(prices))]
    losses = [max(0, prices[i-1] - prices[i]) for i in range(1, len(prices))]
    avg_gain = sum(gains[-14:])/14
    avg_loss = sum(losses[-14:])/14
    rsi = 100 - (100 / (1 + avg_gain/avg_loss)) if avg_loss != 0 else 100

    # EMA trend (20-period)
    ema = sum(prices[-20:])/20

    # Signal logic
    if current_price > vwap and rsi < 70 and current_price > ema:
        side = "buy"
    elif current_price < vwap and rsi > 30 and current_price < ema:
        side = "sell"
    else:
        return None  # no trade

    # Dynamic sizing (2% - 10% of account equity)
    account = client.get_account("USD")
    equity = float(account['balance'])
    size_pct = 0.05  # can adjust dynamically
    size = (equity * size_pct) / current_price

    return {"side": side, "size": round(size, 6), "trail_pct": 0.005}  # 0.5% trailing

# -------------------
# Execute trade
# -------------------
def execute_trade():
    trade = nija_trade_signal()
    if trade:
        order = client.place_order(
            symbol="BTC-USD",
            side=trade["side"],
            type="market",
            size=trade["size"],
            trailing_stop_pct=trade["trail_pct"]
        )
        print("🚀 LIVE TRADE EXECUTED:", order)
    else:
        print("⏸ No trade signal currently.")

# -------------------
# Trailing stop monitor (background)
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
            print("⚠ Trailing stop error:", e)
        time.sleep(5)

# -------------------
# Start background monitor
# -------------------
monitor_thread = threading.Thread(target=trailing_stop_monitor, daemon=True)
monitor_thread.start()
print("🚀 Trailing stop monitor running in background.")

# -------------------
# Main loop (every minute)
# -------------------
while True:
    execute_trade()
    time.sleep(60)  # check every 1 minute
