import sys
sys.path.append("./.venv/lib/python3.13/site-packages")

import coinbase_advanced_py as cb

#!/usr/bin/env python3
import os
import sys
import time
import threading
import traceback
import importlib
import pkgutil
from typing import Any, Callable, Optional

from flask import Flask

# ------------------ Extended Coinbase + Trading helpers ------------------
# (drop this into your existing nija_bot.py replacing the previous import-detection
#  / client init and helper sections)

# Configuration for dynamic allocation (percent values in env are whole numbers)
MIN_ALLOCATION_PCT = float(os.getenv("MIN_ALLOCATION_PCT", "2")) / 100.0   # e.g. 2% -> 0.02
MAX_ALLOCATION_PCT = float(os.getenv("MAX_ALLOCATION_PCT", "10")) / 100.0  # e.g. 10% -> 0.10

# improved import detection honoring override env var
def find_coinbase_client():
    override = os.getenv("COINBASE_MODULE")
    if override:
        candidates = [(override, ["Client", "client.Client"])]
    else:
        candidates = [
            ("coinbase_advanced_py", ["Client", "client.Client"]),
            ("coinbase_advanced", ["Client", "client.Client"]),
            ("coinbase", ["Client", "client.Client"]),
        ]

    for root, attrs in candidates:
        try:
            mod = importlib.import_module(root)
        except ModuleNotFoundError:
            print(f"❌ import failed: module not found: {root}")
            continue
        except Exception as e:
            print(f"⚠️ import {root} raised an exception: {type(e).__name__}: {e}")
            traceback.print_exc()
            continue

        # Try attribute variations
        for attr_path in attrs:
            parts = attr_path.split(".")
            cur = mod
            ok = True
            for p in parts:
                if not hasattr(cur, p):
                    ok = False
                    break
                cur = getattr(cur, p)
            if ok:
                print(f"✅ Found Coinbase client: {root}.{attr_path}")
                return cur, f"{root}.{attr_path}"

        # try submodule client
        try:
            sub = importlib.import_module(f"{root}.client")
            if hasattr(sub, "Client"):
                print(f"✅ Found Coinbase client: {root}.client.Client")
                return getattr(sub, "Client"), f"{root}.client.Client"
        except ModuleNotFoundError:
            pass
        except Exception as e:
            print(f"⚠️ import {root}.client raised {type(e).__name__}: {e}")
            traceback.print_exc()
    return None, None

# MockClient (keep as before)
class MockClient:
    def __init__(self, *a, **k):
        print("⚠️ MockClient created — real Coinbase client not available.")
    def get_account_balances(self):
        return []
    def get_spot_price(self, symbol):
        return {"amount": "0"}
    def get_historic_rates(self, symbol, granularity=60):
        now = int(time.time())
        return [[now - i*60, 0, 0, 0, 0, 0] for i in range(100)]
    def place_order(self, **kwargs):
        raise RuntimeError("LIVE_TRADING disabled or real client not available")

# Initialize client (same logic but slightly reorganized)
ClientClass, import_path = find_coinbase_client()
coinbase_client = None
if ClientClass is None:
    print("❌ No Coinbase client module found. Installed packages (top of pip freeze):")
    for line in debug_installed_packages(100):
        print("   ", line)
    print("ℹ️ The package name provided in requirements should create an importable module like 'coinbase_advanced_py'.")
    coinbase_client = MockClient()
else:
    # Attempt to create client object using keys if present
    if not API_KEY or not API_SECRET:
        print("❌ API_KEY/API_SECRET not set. Please set them in Render environment variables.")
        try:
            coinbase_client = ClientClass()
            print("⚠️ Client created without keys (some methods may be limited).")
        except Exception as e:
            print("⚠️ Failed to create client without keys:", e)
            coinbase_client = MockClient()
    else:
        try:
            try:
                coinbase_client = ClientClass(API_KEY, API_SECRET)
            except TypeError:
                coinbase_client = ClientClass(api_key=API_KEY, api_secret=API_SECRET)
            print(f"✅ Coinbase client created using {import_path}")
        except Exception as e:
            print("❌ Failed to create Coinbase client:", type(e).__name__, e)
            traceback.print_exc()
            coinbase_client = MockClient()

# ------------------ Utility functions ------------------

def safe_get_balances():
    try:
        return coinbase_client.get_account_balances()
    except Exception as e:
        print("❌ get_account_balances error:", type(e).__name__, e)
        return []

def safe_get_spot_price(sym):
    try:
        p = coinbase_client.get_spot_price(sym)
        if isinstance(p, dict) and "amount" in p:
            return float(p["amount"])
        if hasattr(p, "amount"):
            return float(getattr(p, "amount"))
        return float(p)
    except Exception as e:
        print("❌ get_spot_price error for", sym, type(e).__name__, e)
        return 0.0

def safe_get_historic(sym, granularity=60):
    try:
        return coinbase_client.get_historic_rates(sym, granularity=granularity)
    except Exception as e:
        print("❌ get_historic_rates error for", sym, type(e).__name__, e)
        return []

# Estimate account equity in USD using balances list shape:
# Accepts common shapes: list of dicts with 'currency' and 'balance' or similar.
def estimate_account_equity_usd(balances):
    total = 0.0
    try:
        # try common Coinbase shapes
        for b in balances:
            # If shape is dict with 'currency' and 'balance' and 'available'
            if isinstance(b, dict):
                cur = b.get("currency") or b.get("asset") or b.get("asset_id") or None
                # balance can be nested dict or str/num
                bal_val = None
                for k in ("available", "balance", "amount", "qty", "quantity"):
                    v = b.get(k)
                    if v is not None:
                        if isinstance(v, dict) and "amount" in v:
                            bal_val = float(v["amount"])
                        else:
                            try:
                                bal_val = float(v)
                            except Exception:
                                pass
                        break
                if cur is None or bal_val is None:
                    continue
                if cur.upper() in ("USD", "USDC", "USDT", "DAI"):
                    total += bal_val
                else:
                    price = safe_get_spot_price(cur.upper())
                    total += price * bal_val
            else:
                # unknown shape — skip
                continue
    except Exception as e:
        print("❌ estimate_account_equity_usd error:", e)
    return total

# Compute volatility metric (stddev of returns) mapped to allocation
import math, statistics
def compute_volatility_from_historic(historic):
    # historic: list of [time, low, high, open, close, volume] (coinbase-style)
    try:
        closes = []
        for row in historic:
            # some libs return [time, low, high, open, close, volume], some differ
            if len(row) >= 5:
                closes.append(float(row[4]))
            else:
                # if simple list of prices
                closes.append(float(row[-1]))
        if len(closes) < 5:
            return None
        # compute log returns
        returns = []
        for i in range(1, len(closes)):
            if closes[i-1] <= 0:
                continue
            r = math.log(closes[i] / closes[i-1])
            returns.append(r)
        if not returns:
            return None
        return statistics.stdev(returns)
    except Exception as e:
        print("❌ compute_volatility_from_historic error:", e)
        return None

def map_vol_to_pct(stddev, min_pct=MIN_ALLOCATION_PCT, max_pct=MAX_ALLOCATION_PCT):
    """
    Map volatility (stddev) to allocation pct:
    - lower stddev -> higher allocation (more aggressive)
    - higher stddev -> smaller allocation (safer)
    We'll map using a simple heuristic with clamping.
    """
    # set heuristic bounds (these can be tuned)
    LOW_VOL = 0.0005   # very low volatility (aggressive)
    HIGH_VOL = 0.01    # very high volatility (conservative)
    if stddev is None:
        return min(max((min_pct + max_pct) / 2.0, min_pct), max_pct)
    # clamp stddev to range
    s = max(min(stddev, HIGH_VOL), LOW_VOL)
    # invert mapping: stddev near LOW_VOL -> max_pct ; near HIGH_VOL -> min_pct
    ratio = (s - LOW_VOL) / (HIGH_VOL - LOW_VOL)  # 0..1
    pct = max_pct - ratio * (max_pct - min_pct)
    return max(min(pct, max_pct), min_pct)

# Determine USD order size for a symbol (based on current account equity and volatility)
def calculate_order_usd_for_symbol(symbol, balances):
    equity = estimate_account_equity_usd(balances)
    if equity <= 0:
        # Fallback to a small default allocation (so we don't create giant orders)
        fallback_usd = 10.0
        print("⚠️ Unable to determine account equity; using fallback USD allocation:", fallback_usd)
        return fallback_usd

    # fetch recent historic candles
    hist = safe_get_historic(symbol, granularity=60)
    stddev = compute_volatility_from_historic(hist)
    pct = map_vol_to_pct(stddev)
    order_usd = equity * pct
    print(f"Calculated allocation for {symbol}: equity=${equity:.2f} stddev={stddev} pct={pct*100:.2f}% -> order_usd=${order_usd:.2f}")
    return order_usd

# Safe place order wrapper (gates on LIVE_TRADING)
def place_order_safe(symbol, side, size_usd, price=None, order_type="market", **kwargs):
    """
    symbol: "BTC" or "ETH" (bot maps to correct market in exchange API)
    side: "buy" or "sell"
    size_usd: USD size of order (converted to qty)
    price: optional limit price (if None, create market order)
    """
    # Convert USD size -> quantity by fetching spot price
    spot = safe_get_spot_price(symbol)
    if spot <= 0:
        print("❌ Cannot place order: invalid spot price for", symbol, spot)
        return None

    qty = size_usd / spot
    order_payload = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "size": qty,
        "price": price,
        **kwargs
    }
    if not LIVE_TRADING:
        print("SIMULATED ORDER (LIVE_TRADING=false):", order_payload)
        return order_payload

    # ensure real client has place_order
    if hasattr(coinbase_client, "place_order"):
        try:
            print("Placing real order:", order_payload)
            result = coinbase_client.place_order(**order_payload)
            print("Order result:", result)
            return result
        except Exception as e:
            print("❌ place_order failed:", type(e).__name__, e)
            traceback.print_exc()
            return None
    else:
        print("❌ coinbase_client has no place_order method; simulated instead:", order_payload)
        return order_payload

# ------------------ Example trading decision updated ------------------
def bot_cycle_once():
    balances = safe_get_balances()
    print("Balances snapshot:", balances)
    for sym in ("BTC", "ETH"):
        price = safe_get_spot_price(sym)
        print(f"{sym} spot price: {price}")

    # Example: decide to buy BTC if price > 0 (demo)
    # Replace the condition with your actual strategy signals.
    try:
        # Compute USD allocation dynamically for BTC (demo buy)
        order_usd = calculate_order_usd_for_symbol("BTC", balances)
        # Demo: only place half allocation as buy if price > 0 (you will change to your real strategy)
        if order_usd and order_usd > 0:
            # Very important: only place real orders if LIVE_TRADING true. This wrapper enforces it.
            place_order_safe("BTC", "buy", size_usd=order_usd * 0.5)
    except Exception as e:
        print("❌ Error in trade decision:", e)
        traceback.print_exc()

# ------------------ end of patch ------------------
