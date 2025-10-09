# nija_bot.py
# Render-ready Nija Trading Bot — robust vendored import + minimal trading loop

import sys
import os
import time
from datetime import datetime
import traceback

# --- 1) ensure vendor dir is on sys.path ---
VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)

# --- 2) Import coinbase_advanced_py (vendored) ---
try:
    import coinbase_advanced_py as cb  # vendored package expected in vendor/coinbase_advanced_py
    print("✅ Imported vendored coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except Exception as e:
    print("❌ vendored coinbase_advanced_py import failed:", e)
    # Try best-effort runtime install into vendor (may work on some hosts)
    try:
        print("➡️ Attempting pip install to ./vendor ...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--target", VENDOR_DIR, "coinbase-advanced-py==1.8.2"])
        # retry import
        import importlib
        importlib.invalidate_caches()
        import coinbase_advanced_py as cb
        print("✅ Installed and imported coinbase_advanced_py via pip into vendor:", getattr(cb, "__version__", "unknown"))
    except Exception as e2:
        print("❌ Runtime install/import also failed:", e2)
        print("❗ Make sure vendor/coinbase_advanced_py exists (see README). Exiting.")
        raise SystemExit(1)

# --- 3) Load credentials from environment (do NOT commit secrets to git) ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes")
SANDBOX = os.getenv("SANDBOX", "True").lower() in ("1", "true", "yes")
TRADE_SYMBOLS = os.getenv("TRADE_SYMBOLS", "BTC-USD,ETH-USD").split(",")
TRADE_AMOUNT = float(os.getenv("TRADE_AMOUNT", "0.001"))
SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", "10"))

if not API_KEY or not API_SECRET:
    print("⚠️ WARNING: API_KEY/API_SECRET not set. Running in DRY_RUN/mock mode.")
    DRY_RUN = True

# --- 4) Initialize client (try multiple shapes) ---
client = None
api_shape = None
try:
    # common older shape
    client = cb.Client(API_KEY, API_SECRET)
    api_shape = "client"
    print("🚀 Initialized cb.Client()")
except Exception as e:
    # try modern split APIs or other shapes
    try:
        from coinbase_advanced_py import AccountAPI, OrderAPI, MarketAPI  # type: ignore
        account_api = AccountAPI(API_KEY, API_SECRET)
        order_api = OrderAPI(API_KEY, API_SECRET)
        market_api = MarketAPI(API_KEY, API_SECRET)
        api_shape = "split"
        client = {"account": account_api, "order": order_api, "market": market_api}
        print("🚀 Initialized AccountAPI/OrderAPI/MarketAPI")
    except Exception as e2:
        print("⚠️ Coinbase client initialization failed (will use mock client if DRY_RUN):", e2)
        api_shape = "none"

# --- 5) Mock client for dry-run/fallback ---
class MockClient:
    def get_account_balances(self):
        return {"USD": {"available": "1000.0", "hold": "0.0"}}
    def get_product_price(self, symbol):
        return 30000.0 if "BTC" in symbol else 100.0
    def place_market_order(self, symbol, side, size):
        return {"id": "mock-1", "symbol": symbol, "side": side, "size": size, "status": "filled"}

if DRY_RUN or api_shape == "none":
    mock = MockClient()
    client = mock
    api_shape = "mock"
    print("🟡 Using MockClient (DRY_RUN ON)")

# --- 6) Helper wrappers that adapt to the client shape ---
def get_balances():
    try:
        if api_shape == "client":
            return client.get_account_balances()
        if api_shape == "split":
            return client["account"].get_balances()
        if api_shape == "mock":
            return client.get_account_balances()
    except Exception as e:
        print("Failed get_balances:", e)
        return None

def get_price(symbol):
    try:
        if api_shape == "client":
            return client.get_product_price(symbol)
        if api_shape == "split":
            t = client["market"].get_ticker(symbol)
            if isinstance(t, dict):
                return t.get("price") or t.get("last")
            return t
        if api_shape == "mock":
            return client.get_product_price(symbol)
    except Exception as e:
        print("Failed get_price:", e)
        return None

def place_market_order(symbol, side, size):
    try:
        if api_shape == "client":
            return client.place_market_order(symbol, side, size)
        if api_shape == "split":
            return client["order"].place_market_order(symbol=symbol, side=side, size=size)
        if api_shape == "mock":
            return client.place_market_order(symbol, side, size)
    except Exception as e:
        print("Failed place_market_order:", e)
        return None

# --- 7) Minimal trading loop ---
def main():
    print(f"Starting Nija Trading Bot at {datetime.utcnow().isoformat()} (DRY_RUN={DRY_RUN})")
    balances = get_balances()
    print("Balances:", balances)
    symbols = [s.strip() for s in TRADE_SYMBOLS if s.strip()]
    while True:
        for symbol in symbols:
            price = get_price(symbol)
            print(f"{datetime.utcnow().isoformat()} {symbol} price: {price}")
            if not DRY_RUN:
                resp = place_market_order(symbol, "buy", TRADE_AMOUNT)
                print("Order response:", resp)
            else:
                print("DRY_RUN active — no orders placed.")
            time.sleep(1)
        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as ex:
        print("Fatal error:", ex)
        traceback.print_exc()
        raise
