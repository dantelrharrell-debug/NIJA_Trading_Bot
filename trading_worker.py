#!/usr/bin/env python3
"""
trading_worker.py

Run this as a separate process (NOT inside your web server workers).
Example:
  LIVE_TRADING=0 API_KEY=... API_SECRET=... python trading_worker.py

Defaults to dry-run. To enable live trading set LIVE_TRADING=1 and verify keys and sandbox first.
"""

import os
import sys
import time
import signal
import traceback
import importlib
import pkgutil
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# ----------------------------
# Basic logging helper
# ----------------------------
def log(*args, **kwargs):
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    print(ts, *args, **kwargs, flush=True)

# ----------------------------
# Import guard: locate Coinbase client class
# ----------------------------
log("=== coinbase import guard ===")
log("Python:", sys.executable)
log("cwd:", os.getcwd())
log("sys.path (first 8):", sys.path[:8])

CoinbaseClientClass = None
_candidate_pairs = [
    ("coinbase_advanced_py", "CoinbaseAdvanced"),
    ("coinbase_advanced", "CoinbaseAdvanced"),
    ("coinbase", "CoinbaseAdvanced"),
    ("coinbase", "CoinbaseClient"),
    ("coinbase", "Coinbase"),
    ("coinbase", "Client"),
]

for mod_name, cls_name in _candidate_pairs:
    try:
        mod = importlib.import_module(mod_name)
        log(f"INFO: imported module '{mod_name}'")
        cls = getattr(mod, cls_name, None)
        if cls:
            CoinbaseClientClass = cls
            log(f"FOUND: class '{cls_name}' on module '{mod_name}'")
            break
        # If submodule/class file exists: try importing mod_name.cls_name
        try:
            sub = importlib.import_module(f"{mod_name}.{cls_name}")
            cls = getattr(sub, cls_name, None)
            if cls:
                CoinbaseClientClass = cls
                log(f"FOUND: class '{cls_name}' in submodule '{mod_name}.{cls_name}'")
                break
        except Exception:
            pass
    except Exception as e:
        log(f"INFO: cannot import {mod_name}: {type(e).__name__}: {e}")

if CoinbaseClientClass is None:
    log("WARNING: did not find expected Coinbase client class. Installed site-packages matching coin/base/advanced:")
    try:
        for p in pkgutil.iter_modules():
            name = p.name.lower()
            if any(k in name for k in ("coin", "base", "advanced")):
                log(" -", p.name)
    except Exception:
        traceback.print_exc()
    log("ERROR: Coinbase client not found. Exiting.")
    sys.exit(1)

log("=== coinbase import guard finished ===")

# ----------------------------
# ENV / config
# ----------------------------
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") in ("1", "true", "True")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM_B64 = os.getenv("API_PEM_B64", None)

SYMBOL = os.getenv("SYMBOL", "BTC-USD")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_S", "60"))  # seconds
SIZE_PCT = float(os.getenv("SIZE_PCT", "0.05"))  # default 5% of equity
MAX_SIZE_PCT = float(os.getenv("MAX_SIZE_PCT", "0.10"))  # never exceed 10% of equity in single order
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
EMA_PERIOD = int(os.getenv("EMA_PERIOD", "20"))
VWAP_LOOKBACK = int(os.getenv("VWAP_LOOKBACK", "50"))
TRAIL_PCT = float(os.getenv("TRAIL_PCT", "0.005"))  # 0.5%

log("Config:", {"LIVE_TRADING": LIVE_TRADING, "SYMBOL": SYMBOL, "CHECK_INTERVAL": CHECK_INTERVAL})

# ----------------------------
# Instantiate client
# ----------------------------
try:
    # attempt several constructor signatures (some SDKs use different param names)
    try:
        client = CoinbaseClientClass(api_key=API_KEY, api_secret=API_SECRET, api_pem_b64=API_PEM_B64)
    except TypeError:
        # try alternate names
        client = CoinbaseClientClass(key=API_KEY, secret=API_SECRET)
    log("INFO: Coinbase client instantiated:", type(client).__name__)
except Exception:
    log("ERROR: failed to instantiate Coinbase client:")
    traceback.print_exc()
    sys.exit(1)

# ----------------------------
# Utilities: safe order wrapper (dry-run by default)
# ----------------------------
_order_sim_counter = 0

def place_order_safe(client, **kwargs) -> Dict[str, Any]:
    global _order_sim_counter
    if not LIVE_TRADING:
        _order_sim_counter += 1
        sim = {
            "id": f"sim-{int(time.time())}-{_order_sim_counter}",
            "status": "simulated",
            "side": kwargs.get("side"),
            "symbol": kwargs.get("symbol"),
            "size": kwargs.get("size"),
            "type": kwargs.get("type", "market"),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        log("DRY-RUN order:", sim)
        return sim

    # LIVE_TRADING path
    try:
        resp = client.place_order(**kwargs)
        log("LIVE order response:", resp)
        return resp
    except Exception:
        log("ERROR placing live order:")
        traceback.print_exc()
        raise

# ----------------------------
# Market data helper functions - adapt to the SDK you have
# ----------------------------
def get_historic_closes(symbol: str, granularity: int = 60, limit: int = 200) -> List[float]:
    """
    Try common method names that coinbase clients expose for historic candles.
    Returns list of close prices (floats), newest last.
    """
    # Try client's methods in order of likely names; adapt as needed based on SDK
    cand_calls = [
        ("get_historic_candles", ("symbol", granularity, limit)),  # earlier examples
        ("get_historic_rates", (symbol, granularity, limit)),
        ("get_klines", (symbol, granularity, limit)),
        ("historic_candles", (symbol, granularity, limit)),
        ("get_candles", (symbol, granularity, limit)),
    ]
    for method_name, args in cand_calls:
        method = getattr(client, method_name, None)
        if callable(method):
            try:
                res = method(*args if args else ())
                # try to normalize: if list of candles where candle[-1] or candle[4] is close
                closes = []
                if isinstance(res, list):
                    for c in res:
                        if isinstance(c, (list, tuple)) and len(c) >= 5:
                            # assume [time, open, high, low, close, ...]
                            closes.append(float(c[4]))
                        elif isinstance(c, dict) and ("close" in c):
                            closes.append(float(c["close"]))
                elif isinstance(res, dict) and "candles" in res:
                    for c in res["candles"]:
                        closes.append(float(c.get("close") or c.get("price") or c[4]))
                if len(closes) > 0:
                    return closes[-limit:]
            except Exception as e:
                log(f"DEBUG: method {method_name} raised {type(e).__name__}: {e}")
                # continue trying others
    # As last resort, try ticker price repeated
    try:
        ticker = getattr(client, "get_ticker", None)
        if callable(ticker):
            t = ticker(symbol)
            price = float(t.get("price") if isinstance(t, dict) else float(t))
            # return list of same price (not ideal but keeps code safe)
            return [price] * limit
    except Exception:
        pass
    raise RuntimeError("Could not fetch historic closes from client - adapt get_historic_closes for your SDK")

# ----------------------------
# Indicator calculations
# ----------------------------
def calc_vwap(prices: List[float]) -> float:
    # simple unweighted average as placeholder (true VWAP needs volume)
    return sum(prices) / len(prices)

def calc_ema(prices: List[float], period: int) -> float:
    # simple EMA: use SMA then smoothing
    if len(prices) < period:
        return sum(prices) / len(prices)
    sma = sum(prices[-period:]) / period
    k = 2 / (period + 1)
    ema = sma
    for price in prices[-period:]:
        ema = price * k + ema * (1 - k)
    return ema

def calc_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    if len(prices) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, len(prices)):
        d = prices[i] - prices[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

# ----------------------------
# Trade signal
# ----------------------------
def nija_trade_signal() -> Optional[Dict[str, Any]]:
    try:
        closes = get_historic_closes(SYMBOL, granularity=60, limit=VWAP_LOOKBACK)
    except Exception as e:
        log("ERROR fetching candles:", e)
        return None

    if len(closes) < max(RSI_PERIOD + 1, EMA_PERIOD, 10):
        log("INFO: not enough data for indicators:", len(closes))
        return None

    current_price = float(closes[-1])
    vwap = calc_vwap(closes[-VWAP_LOOKBACK:])
    ema = calc_ema(closes, EMA_PERIOD)
    rsi = calc_rsi(closes, RSI_PERIOD)
    if rsi is None:
        log("INFO: RSI not available (insufficient data).")
        return None

    log(f"Indicators — price: {current_price:.2f}, vwap: {vwap:.2f}, ema{EMA_PERIOD}: {ema:.2f}, rsi{RSI_PERIOD}: {rsi:.2f}")

    # Very conservative signal logic. Adjust for your strategy.
    if current_price > vwap and rsi < 70 and current_price > ema:
        side = "buy"
    elif current_price < vwap and rsi > 30 and current_price < ema:
        side = "sell"
    else:
        return None

    # Fetch account USD balance safely
    equity = 0.0
    try:
        get_acc = getattr(client, "get_account", None) or getattr(client, "get_wallet", None)
        if callable(get_acc):
            acct = get_acc("USD")
            # try to extract balance from common shapes
            if isinstance(acct, dict):
                # many SDKs: acct['balance'] or acct['available'] or acct['balance']['amount']
                if "balance" in acct and isinstance(acct["balance"], (dict, str, float)):
                    b = acct["balance"]
                    if isinstance(b, dict) and "amount" in b:
                        equity = float(b["amount"])
                    else:
                        equity = float(b)
                elif "available" in acct:
                    equity = float(acct["available"])
                elif "amount" in acct:
                    equity = float(acct["amount"])
            elif isinstance(acct, (int, float, str)):
                equity = float(acct)
    except Exception:
        log("DEBUG: fetching USD account failed; defaulting equity to 1000 (simulation).")
        equity = 1000.0

    if equity <= 0:
        equity = 1000.0  # fallback for dry-run or missing account info

    size_pct = min(SIZE_PCT, MAX_SIZE_PCT)
    size = (equity * size_pct) / current_price
    size = round(size, 6)

    return {"side": side, "size": size, "trail_pct": TRAIL_PCT, "price": current_price}

# ----------------------------
# Main loop with backoff and graceful shutdown
# ----------------------------
_stop_requested = False

def _signal_handler(sig, frame):
    global _stop_requested
    log("Signal received:", sig, " — shutting down gracefully...")
    _stop_requested = True

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

def trading_loop():
    backoff = 1
    while not _stop_requested:
        try:
            signal_data = nija_trade_signal()
            if signal_data:
                log("Trade signal:", signal_data)
                # Build order kwargs - adapt fields to your client
                order_kwargs = {
                    "symbol": SYMBOL,
                    "side": signal_data["side"],
                    "type": "market",
                    "size": signal_data["size"],
                }
                # Use safe wrapper
                try:
                    resp = place_order_safe(client, **order_kwargs)
                    log("Order result:", resp)
                except Exception:
                    log("Order failed — continuing.")
            else:
                log("No trade signal.")

            # reset backoff on success or normal iteration
            backoff = 1
            # Wait interval, but exit promptly if stop requested
            for _ in range(int(CHECK_INTERVAL)):
                if _stop_requested:
                    break
                time.sleep(1)
        except Exception as e:
            log("Unhandled error in trading loop:", type(e).__name__, e)
            traceback.print_exc()
            time.sleep(backoff)
            backoff = min(backoff * 2, 300)  # cap backoff at 5 minutes

    log("Trading loop stopped.")

# ----------------------------
# Entry point
# ----------------------------
if __name__ == "__main__":
    log("Starting trading_worker")
    if not LIVE_TRADING:
        log("DRY-RUN mode: no live orders will be placed. Set LIVE_TRADING=1 to enable (use extreme caution).")
    else:
        log("LIVE_TRADING=1 — LIVE ORDERS WILL BE PLACED. Ensure keys and sandbox verified.")

    try:
        trading_loop()
    except KeyboardInterrupt:
        log("KeyboardInterrupt received — exiting.")
    except Exception:
        log("Fatal error:")
        traceback.print_exc()
    log("Exited.")
