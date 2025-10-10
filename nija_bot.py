#!/usr/bin/env python3
"""
Nija Trading Bot - restored main script.

How to use:
 - Ensure coinbase_advanced_py is available:
     * Recommended: vendor/coinbase_advanced_py in your repo (and start.sh loads vendor)
     * Or: include coinbase-advanced-py==1.8.2 in requirements.txt and let start.sh pip install it
 - Set environment variables (Render > Environment):
     API_KEY, API_SECRET, SANDBOX (True/False), DRY_RUN (True/False),
     TRADE_SYMBOLS (comma-separated, e.g. "BTC-USD,ETH-USD"),
     TRADE_AMOUNT (per-symbol float), SLEEP_INTERVAL (seconds)
 - Start command: `bash start.sh` (or run `python3 nija_bot.py` locally)
"""

import sys
import os
import time
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
VENDOR_DIR = str(ROOT / "vendor")

# Add vendor dir first so a vendored package takes precedence
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)
    print("✅ Added vendor to sys.path:", VENDOR_DIR)

# Try to import dotenv (optional - helpful locally)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env (if present)")
except Exception:
    # Not critical on Render; continue
    pass

# ---------------------------
# Import coinbase package
# ---------------------------
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except ModuleNotFoundError as e:
    print("❌ Module coinbase_advanced_py not found in vendor or site-packages.")
    print("   Make sure vendor/coinbase_advanced_py exists, or add coinbase-advanced-py to requirements.txt")
    raise SystemExit(1)
except Exception as e:
    print("❌ Unexpected error importing coinbase_advanced_py:", type(e).__name__, e)
    raise SystemExit(1)

# ---------------------------
# Read environment variables
# ---------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SANDBOX = os.getenv("SANDBOX", "True").lower() in ("1", "true", "yes")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes")

# TRADE_SYMBOLS can be "BTC-USD,ETH-USD" etc.
TRADE_SYMBOLS = [s.strip() for s in os.getenv("TRADE_SYMBOLS", "BTC-USD").split(",") if s.strip()]
# TRADE_AMOUNT is per-symbol if single value, or can be comma-separated matching symbols
TRADE_AMOUNT_RAW = os.getenv("TRADE_AMOUNT", "10")
SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", "10"))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0"))  # e.g. 0.02 for 2%
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "0"))  # e.g. 0.05 for 5%

# Parse TRADE_AMOUNT into list matching symbols (fallback to single value)
amounts = []
if "," in TRADE_AMOUNT_RAW:
    parts = [p.strip() for p in TRADE_AMOUNT_RAW.split(",")]
    for p in parts:
        try:
            amounts.append(float(p))
        except:
            amounts.append(0.0)
else:
    try:
        single_amt = float(TRADE_AMOUNT_RAW)
    except:
        single_amt = 0.0
    amounts = [single_amt] * len(TRADE_SYMBOLS)

if not API_KEY or not API_SECRET:
    print("❌ Missing API_KEY or API_SECRET environment variables.")
    if not DRY_RUN:
        raise SystemExit(1)
    else:
        print("⚠️ Continuing in DRY_RUN mode without API keys.")

# ---------------------------
# Initialize Coinbase client safely
# ---------------------------
client = None
try:
    # Try the common constructor
    # Many wrappers use cb.Client(key, secret, sandbox=...)
    client = cb.Client(API_KEY, API_SECRET, sandbox=SANDBOX) if hasattr(cb, "Client") else None
    if client is None:
        # Try alternate names / factory
        for name in dir(cb):
            if name.lower().startswith("client") or name.lower().startswith("coinbase"):
                attr = getattr(cb, name)
                try:
                    client = attr(API_KEY, API_SECRET, sandbox=SANDBOX)
                    break
                except Exception:
                    continue
    if client is None:
        print("❌ Could not construct a client object from coinbase_advanced_py. Inspecting module attributes:")
        print(dir(cb)[:200])
        raise SystemExit(1)
    print("🚀 Coinbase client initialized:", type(client))
except TypeError as te:
    print("❌ TypeError when initializing client:", te)
    print("Module exposes:", dir(cb)[:200])
    raise SystemExit(1)
except Exception as e:
    print("❌ Error initializing coinbase client:", type(e).__name__, e)
    if not DRY_RUN:
        raise SystemExit(1)

# ---------------------------
# Helper: get price for a product symbol
# Attempts a few common method names used by wrappers
# ---------------------------
def get_price_for_symbol(client, symbol):
    # Attempt: get_product_price(product_id)
    if hasattr(client, "get_product_price"):
        try:
            return client.get_product_price(symbol)
        except Exception:
            pass
    # Attempt: get_price(product_id) or get_ticker
    if hasattr(client, "get_price"):
        try:
            return client.get_price(symbol)
        except Exception:
            pass
    if hasattr(client, "get_ticker"):
        try:
            return client.get_ticker(symbol)
        except Exception:
            pass
    # Attempt: client public REST call - sometimes client has .public or .rest
    for attr_name in ("public", "rest", "api"):
        if hasattr(client, attr_name):
            sub = getattr(client, attr_name)
            for fn in ("get_product_price", "get_price", "get_ticker", "ticker", "product_ticker"):
                if hasattr(sub, fn):
                    try:
                        return getattr(sub, fn)(symbol)
                    except Exception:
                        continue
    # if nothing worked, raise informative error
    raise RuntimeError("No known price method on client. Available attrs: " + ", ".join(dir(client)[:80]))

# ---------------------------
# Example: fetch balances (non-blocking)
# ---------------------------
try:
    if client:
        if hasattr(client, "get_account_balances"):
            try:
                balances = client.get_account_balances()
                print("💰 Balances:", balances)
            except Exception as e:
                print("ℹ️ get_account_balances failed:", type(e).__name__, e)
        elif hasattr(client, "get_accounts"):
            try:
                accounts = client.get_accounts()
                print("💰 Accounts:", accounts)
            except Exception as e:
                print("ℹ️ get_accounts failed:", type(e).__name__, e)
        else:
            print("ℹ️ No balance method found on client; continuing.")
except Exception as e:
    print("ℹ️ Balance check error:", type(e).__name__, e)

# ---------------------------
# Trading loop (placeholder)
# This will only PLACE ORDERS if DRY_RUN is False and the client exposes order methods.
# ---------------------------
print("🔁 Entering main loop. DRY_RUN =", DRY_RUN, "SANDBOX =", SANDBOX)
try:
    while True:
        for i, symbol in enumerate(TRADE_SYMBOLS):
            amt = amounts[i] if i < len(amounts) else amounts[0] if amounts else 0.0
            try:
                price = get_price_for_symbol(client, symbol)
            except Exception as e:
                print(f"❌ Could not fetch price for {symbol}:", type(e).__name__, e)
                continue

            print(f"📈 {symbol} price:", price, "| planned amount:", amt)

            # Example trade logic (placeholder). Replace with your strategy.
            # To actually place orders the client must expose a method such as place_market_order or place_order.
            order_placed = False
            if not DRY_RUN and amt > 0:
                # Try several common order methods
                for fn in ("place_market_order", "place_order", "create_order", "submit_order"):
                    if hasattr(client, fn):
                        try:
                            print(f"➡️ Attempting {fn} for {symbol} amount {amt} ...")
                            res = getattr(client, fn)(symbol, "buy", amt)  # many libs use (product_id, side, size/amount)
                            print("✅ Order result:", res)
                            order_placed = True
                            break
                        except Exception as e:
                            print(f"⚠️ {fn} raised:", type(e).__name__, e)
                if not order_placed:
                    print("⚠️ No known order placement method found on client or all attempts failed. Check client API.")
            else:
                print("ℹ️ DRY_RUN ON or zero amount — no real order placed.")

        time.sleep(max(1, SLEEP_INTERVAL))
except KeyboardInterrupt:
    print("🛑 User stopped the bot")
except Exception as e:
    print("❌ Unexpected error in main loop:", type(e).__name__, e)
    raise
