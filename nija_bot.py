import sys
import os
import time
from datetime import datetime

# -----------------------------
# 1️⃣ Add vendor folder to sys.path
# -----------------------------
VENDOR_DIR = os.path.join(os.path.dirname(__file__), "vendor")
if VENDOR_DIR not in sys.path:
    sys.path.insert(0, VENDOR_DIR)
    print(f"✅ Added vendor folder to sys.path: {VENDOR_DIR}")

# -----------------------------
# 2️⃣ Import coinbase_advanced_py modules
# -----------------------------
try:
    from coinbase_advanced_py import AccountAPI, OrderAPI, MarketAPI
    print("✅ Imported coinbase_advanced_py modules")
except ModuleNotFoundError:
    raise SystemExit("❌ Module coinbase_advanced_py not found. Make sure 'vendor/coinbase_advanced_py' exists.")

# -----------------------------
# 3️⃣ Load API keys from environment
# -----------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET environment variables")

# -----------------------------
# 4️⃣ Initialize APIs
# -----------------------------
account_api = AccountAPI(API_KEY, API_SECRET)
order_api = OrderAPI(API_KEY, API_SECRET)
market_api = MarketAPI(API_KEY, API_SECRET)

print("🚀 Nija Trading Bot initialized at", datetime.utcnow().isoformat())

# -----------------------------
# 5️⃣ Example: fetch balances
# -----------------------------
try:
    balances = account_api.get_balances()
    print("💰 Account balances:", balances)
except Exception as e:
    print("❌ Failed to fetch balances:", e)

# -----------------------------
# 6️⃣ Recent upgrades / features
# -----------------------------
def place_order(symbol: str, side: str, size: float, price: float = None):
    """
    Place a market or limit order.
    - side: 'buy' or 'sell'
    - size: amount of asset to trade
    - price: for limit orders (optional)
    """
    try:
        if price:
            response = order_api.place_limit_order(symbol=symbol, side=side, size=size, price=price)
            print(f"📌 Limit order placed: {response}")
        else:
            response = order_api.place_market_order(symbol=symbol, side=side, size=size)
            print(f"📌 Market order placed: {response}")
        return response
    except Exception as e:
        print(f"❌ Failed to place {side} order for {symbol}: {e}")
        return None

def monitor_market(symbol: str, interval: float = 5.0):
    """
    Simple market monitor: prints current price every `interval` seconds.
    """
    try:
        while True:
            ticker = market_api.get_ticker(symbol)
            print(f"📈 {datetime.utcnow().isoformat()} - {symbol} price: {ticker['price']}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("🛑 Market monitoring stopped by user")
    except Exception as e:
        print("❌ Error in market monitoring:", e)

# -----------------------------
# 7️⃣ Bot logic placeholder
# -----------------------------
# Example usage:
# place_order("BTC-USD", "buy", 0.001)
# monitor_market("BTC-USD", 10)
