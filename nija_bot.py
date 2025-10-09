# nija_bot.py
# Nija Trading Bot - Render-ready, vendored coinbase_advanced_py support.
# Python source must be UTF-8. This file avoids concatenation and duplicate imports.

import sys
import os
import time
from datetime import datetime

# -----------------------------
# 1) Add vendor folder to sys.path
# -----------------------------
VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)

# -----------------------------
# 2) Import coinbase_advanced_py (robust)
# -----------------------------
try:
    # Prefer explicit API classes if available
    from coinbase_advanced_py import AccountAPI, OrderAPI, MarketAPI  # type: ignore
    HAS_NEW_API = True
except Exception:
    HAS_NEW_API = False

try:
    import coinbase_advanced_py as cb  # type: ignore
except ModuleNotFoundError:
    raise SystemExit("ERROR: vendored module 'vendor/coinbase_advanced_py' not found. Place extracted package there and retry.")

print("Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))

# -----------------------------
# 3) Load API creds from env
# -----------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SANDBOX = os.getenv("SANDBOX", "True").lower() in ("1", "true", "yes")

if not API_KEY or not API_SECRET:
    raise SystemExit("ERROR: API_KEY and API_SECRET must be set in environment variables.")

# -----------------------------
# 4) Initialize appropriate client objects
# -----------------------------
try:
    if HAS_NEW_API:
        account_api = AccountAPI(API_KEY, API_SECRET)
        order_api = OrderAPI(API_KEY, API_SECRET)
        market_api = MarketAPI(API_KEY, API_SECRET)
        print("Initialized AccountAPI/OrderAPI/MarketAPI")
    else:
        # fallback for older vendored package that exposes Client
        client = cb.Client(API_KEY, API_SECRET)
        print("Initialized cb.Client")
except Exception as e:
    raise SystemExit(f"ERROR initializing Coinbase objects: {e}")

# -----------------------------
# 5) Example helper functions (safe)
# -----------------------------
def get_balances():
    try:
        if HAS_NEW_API:
            return account_api.get_balances()
        else:
            return client.get_account_balances()
    except Exception as exc:
        print("Failed to fetch balances:", exc)
        return None

def get_price(symbol="BTC-USD"):
    try:
        if HAS_NEW_API:
            ticker = market_api.get_ticker(symbol)
            # market_api.get_ticker may return different shapes; try a few keys
            if isinstance(ticker, dict):
                return ticker.get("price") or ticker.get("last") or ticker.get("price_usd")
            return ticker
        else:
            return client.get_product_price(symbol)
    except Exception as exc:
        print("Failed to fetch price:", exc)
        return None

def place_market_order(symbol, side, size):
    try:
        if HAS_NEW_API:
            return order_api.place_market_order(symbol=symbol, side=side, size=size)
        else:
            return client.place_market_order(symbol, side, size)
    except Exception as exc:
        print("Failed to place order:", exc)
        return None

# -----------------------------
# 6) Minimal main loop (safe defaults)
# -----------------------------
def main():
    print(f"Starting Nija Trading Bot at {datetime.utcnow().isoformat()} (sandbox={SANDBOX})")
    balances = get_balances()
    print("Balances:", balances)
    symbol = os.getenv("TRADE_SYMBOL", "BTC-USD")
    while True:
        price = get_price(symbol)
        print(f"{datetime.utcnow().isoformat()} - {symbol} price: {price}")
        # Demo: don't actually trade unless DRY_RUN is unset to False
        dry_run = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes")
        if not dry_run:
            # Example market buy for demonstration (small size)
            resp = place_market_order(symbol, "buy", float(os.getenv("TRADE_AMOUNT", "0.001")))
            print("Order response:", resp)
        else:
            print("Dry run enabled — no orders placed.")
        time.sleep(int(os.getenv("SLEEP_INTERVAL", "10")))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as e:
        print("Fatal error in main:", e)
        raise
