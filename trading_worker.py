#!/usr/bin/env python3
"""
trading_worker.py

Run separately from your web process:
  LIVE_TRADING=0 API_KEY=... API_SECRET=... python trading_worker.py

Defaults to dry-run. Set LIVE_TRADING=1 only when you are certain.
"""

from __future__ import annotations
import os
import sys
import time
import signal
import traceback
import importlib
import pkgutil
from typing import Any, Dict, List, Optional

def log(*args, **kwargs):
    prefix = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    print(prefix, *args, **kwargs, flush=True)

# ----------------------------
# Import/inspection guard
# ----------------------------
log("=== coinbase import & inspection guard ===")
log("Python executable:", sys.executable)
log("cwd:", os.getcwd())
log("sys.path[:8]:", sys.path[:8])

CoinbaseClientClass = None
_candidates = [
    ("coinbase_advanced_py", "CoinbaseAdvanced"),
    ("coinbase_advanced", "CoinbaseAdvanced"),
    ("coinbase", "CoinbaseAdvanced"),
    ("coinbase", "CoinbaseClient"),
    ("coinbase", "Coinbase"),
    ("coinbase", "Client"),
]

for mod_name, cls_name in _candidates:
    try:
        mod = importlib.import_module(mod_name)
        log(f"INFO: imported module '{mod_name}'")
        cls = getattr(mod, cls_name, None)
        if cls:
            CoinbaseClientClass = cls
            log(f"FOUND: class '{cls_name}' on module '{mod_name}'")
            break
        # try submodule
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
        log(f"DEBUG: cannot import {mod_name}: {type(e).__name__}: {e}")

if CoinbaseClientClass is None:
    log("WARNING: could not locate a Coinbase client class. Installed packages (filtered):")
    try:
        for p in pkgutil.iter_modules():
            name = p.name.lower()
            if any(k in name for k in ("coin", "base", "advanced")):
                log(" -", p.name)
    except Exception:
        traceback.print_exc()
    log("ERROR: coinbase client import failed. Adjust guard for your SDK.")
    sys.exit(1)

log("=== import guard finished ===")

# ----------------------------
# Config
# ----------------------------
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") in ("1", "true", "True")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM_B64 = os.getenv("API_PEM_B64", None)

SYMBOL = os.getenv("SYMBOL", "BTC-USD")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_S", "60"))
SIZE_PCT = float(os.getenv("SIZE_PCT", "0.05"))
MAX_SIZE_PCT = float(os.getenv("MAX_SIZE_PCT", "0.10"))
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
EMA_PERIOD = int(os.getenv("EMA_PERIOD", "20"))
VWAP_LOOKBACK = int(os.getenv("VWAP_LOOKBACK", "50"))
TRAIL_PCT = float(os.getenv("TRAIL_PCT", "0.005"))

log("Config:", {
    "LIVE_TRADING": LIVE_TRADING,
    "SYMBOL": SYMBOL,
    "CHECK_INTERVAL": CHECK_INTERVAL,
    "SIZE_PCT": SIZE_PCT,
})

# ----------------------------
# Instantiate client (try several ctor signatures)
# ----------------------------
try:
    try:
        client = CoinbaseClientClass(api_key=API_KEY, api_secret=API_SECRET, api_pem_b64=API_PEM_B64)
    except TypeError:
        try:
            client = CoinbaseClientClass(key=API_KEY, secret=API_SECRET)
        except TypeError:
            client = CoinbaseClientClass()
    log("INFO: Coinbase client instantiated:", type(client).__name__)
except Exception:
    log("ERROR: failed to instantiate Coinbase client:")
    traceback.print_exc()
    sys.exit(1)

# ----------------------------
# Safe order wrapper (dry-run by default)
# ----------------------------
_order_sim_counter = 0
def place_order_safe(**kwargs) -> Dict[str, Any]:
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

    place_fn = getattr(client, "place_order", None) or getattr(client, "create_order", None)
    if not callable(place_fn):
        raise RuntimeError("Coinbase client has no place_order/create_order method; adapt wrapper.")
    try:
        resp = place_fn(**kwargs)
        log("LIVE order response:", resp)
        return resp
    except Exception:
        log("ERROR placing live order:")
        traceback.print_exc()
        raise

# ----------------------------
# Market data helper
# ----------------------------
def get_historic_closes(symbol: str, granularity: int = 60, limit: int = 200) -> List[float]:
    candidate_calls = [
        ("get_historic_candles", (symbol, granularity, limit)),
        ("get_historic_rates", (symbol, granularity, limit)),
        ("get_candles", (symbol, granularity, limit)),
        ("historic_candles", (symbol, granularity, limit)),
        ("get_klines", (symbol, granularity, limit)),
    ]
    for method_name, args in candidate_calls:
        method = getattr(client, method_name, None)
        if callable(method):
            try:
                res = method(*args)
                closes: List[float] = []
                if isinstance(res, list):
                    for c in res:
                        if isinstance(c, (list, tuple)) and len(c) >= 5:
                            closes.append(float(c[4]))
                        elif isinstance(c, dict) and "close" in c:
                            closes.append(float(c["close"]))
                elif isinstance(res, dict):
                    if "candles" in res and isinstance(res["candles"], list):
                        for c in res["candles"]:
                            if isinstance(c, dict):
                                closes.append(float(c.get("close") or c.get("price") or 0))
                            elif isinstance(c, (list, tuple)) and len(c) >= 5:
                                closes.append(float(c[4]))
                if closes:
                    return closes[-limit:]
            except Exception as e:
                log(f"DEBUG: {method_name} raised {type(e).__name__}: {e}")
                continue

    ticker_fn = getattr(client, "get_ticker", None) or getattr(client, "ticker", None)
    if callable(ticker_fn):
        try:
            t = ticker_fn(SYMBOL)
            price = None
            if isinstance(t, dict):
                price = t.get("price") or t.get("last") or t.get("close")
            else:
                price = t
            price = float(price)
            return [price] * limit
        except Exception:
            log("DEBUG: ticker fallback failed.")
    raise RuntimeError("Could not fetch historic closes — adapt get_historic_closes for your SDK")

# ----------------------------
# Indicators
# ----------------------------
def calc_vwap(prices: List[float]) -> float:
    return sum(prices) / len(prices)

def calc_ema(prices: List[float], period: int) -> float:
    if len(prices) < period:
        return sum(prices) / len(prices)
    k = 2 / (period + 1)
    ema = sum(prices[-period:]) / period
    for price in prices[-period:]:
        ema = price * k + ema * (1 - k)
    return ema

def calc_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    if len(prices) < period + 1:
        return None
    gains, losses = [], []
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
# Account helper
# ----------------------------
def get_usd_equity() -> float:
    get_acc_fn = getattr(client, "get_account", None) or getattr(client, "get_wallet", None) or getattr(client, "get_balance", None)
    if callable(get_acc_fn):
        try:
            acct = get_acc_fn("USD")
            if isinstance(acct, dict):
                if "balance" in acct:
                    b = acct["balance"]
                    if isinstance(b, dict) and "amount" in b:
                        return float(b["amount"])
                    return float(b)
                if "available" in acct:
                    return float(acct["available"])
                if "amount" in acct:
                    return float(acct["amount"])
            elif isinstance(acct, (int, float, str)):
                return float(acct)
        except Exception:
            log("DEBUG: get_usd_equity parsing failed; falling through.")
    log("INFO: USD equity not found; defaulting to 1000 for simulation.")
    return 1000.0

# ----------------------------
# Strategy: Nija Signal
# ----------------------------
def nija_trade_signal() -> Optional[Dict[str, Any]]:
    try:
        closes = get_historic_closes(SYMBOL, granularity=60, limit=VWAP_LOOKBACK)
    except Exception as e:
        log("ERROR fetching candles:", e)
        return None

    if len(closes) < max(RSI_PERIOD + 1, EMA_PERIOD, 10):
        log("INFO: not enough data:", len(closes))
        return None

    current_price = float(closes[-1])
    vwap = calc_vwap(closes[-VWAP_LOOKBACK:])
    ema = calc_ema(closes, EMA_PERIOD)
    rsi = calc_rsi(closes, RSI_PERIOD)
    if rsi is None:
        return None

    log(f"IND: price={current_price:.2f}, vwap={vwap:.2f}, ema{EMA_PERIOD}={ema:.2f}, rsi{RSI_PERIOD}={rsi:.2f}")

    side = None
    if current_price > vwap and rsi < 70 and current_price > ema:
        side = "buy"
    elif current_price < vwap and rsi > 30 and current_price < ema:
        side = "sell"
    else:
        return None

    equity = get_usd_equity() or 1000.0
    pct = min(SIZE_PCT, MAX_SIZE_PCT)
    size = round((equity * pct) / current_price, 6)
    return {"side": side, "size": size, "trail_pct": TRAIL_PCT, "price": current_price}

# ----------------------------
# Shutdown flag
# ----------------------------
_stop_requested = False
def _signal_handler(sig, frame):
    global _stop_requested
    log("Signal received:", sig, " — shutting down...")
    _stop_requested = True

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

# ----------------------------
# Main trading loop
# ----------------------------
def trading_loop():
    backoff = 1
    while not _stop_requested:
        try:
            signal_data = nija_trade_signal()
            if signal_data:
                log("Trade signal:", signal_data)
                order_kwargs = {
                    "symbol": SYMBOL,
                    "side": signal_data["side"],
                    "type": "market",
                    "size": signal_data["size"],
                }
                try:
                    resp = place_order_safe(**order_kwargs)
                    log("Order response:", resp)
                except Exception:
                    log("Order placement failed; see stack.")
            else:
                log("No trade signal.")

            backoff = 1
            slept = 0
            while slept < CHECK_INTERVAL and not _stop_requested:
                time.sleep(1)
                slept += 1

        except Exception as e:
            log("Unhandled error in trading loop:", type(e).__name__, e)
            traceback.print_exc()
            time.sleep(backoff)
            backoff = min(backoff * 2, 300)

    log("Trading loop exiting cleanly.")

# ----------------------------
# Entry point
# ----------------------------
if __name__ == "__main__":
    log("Starting trading_worker.")
    if not LIVE_TRADING:
        log("DRY-RUN mode (no real orders).")
    else:
        log("WARNING: LIVE_TRADING enabled — orders WILL be placed.")
    try:
        trading_loop()
    except KeyboardInterrupt:
        log("Interrupted, exiting.")
    except Exception:
        log("Fatal error:")
        traceback.print_exc()
    log("Exited.")
