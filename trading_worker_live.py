#!/usr/bin/env python3
import sys
import os

# -----------------------------
# Ensure virtualenv path is first
# -----------------------------
VENV_PATH = '/app/.venv/lib/python3.11/site-packages'
if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)

# -----------------------------
# Test import
# -----------------------------
try:
    from coinbase_advanced import CoinbaseClient
    print("✅ coinbase_advanced module imported successfully")
except ModuleNotFoundError as e:
    print(f"❌ coinbase_advanced not found: {e}")
    sys.exit(1)

# -----------------------------
# Load env variables
# -----------------------------
from dotenv import load_dotenv
load_dotenv()

# -----------------------------
# Optional: test client connection
# -----------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSPHRASE = os.getenv("API_PASSPHRASE")  # if needed

try:
    client = CoinbaseClient(api_key=API_KEY, api_secret=API_SECRET, passphrase=API_PASSPHRASE)
    print("✅ Coinbase client initialized")
except Exception as e:
    print(f"❌ Failed to initialize Coinbase client: {e}")
    sys.exit(1)

#!/usr/bin/env python3
import os
import time
from datetime import datetime
from coinbase_advanced_py import CoinbaseClient

# -----------------------
# Environment & config
# -----------------------
SANDBOX = os.getenv("SANDBOX", "True").lower() == "true"
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSPHRASE = os.getenv("API_PASSPHRASE")

TRADE_SYMBOL = os.getenv("TRADE_SYMBOL", "BTC-USD")
TRADE_SIZE = float(os.getenv("TRADE_SIZE", 0.001))  # amount in crypto
TRADE_INTERVAL = int(os.getenv("TRADE_INTERVAL", 60))  # seconds between trades

# -----------------------
# Initialize client
# -----------------------
try:
    client = CoinbaseClient(
        key=API_KEY,
        secret=API_SECRET,
        passphrase=API_PASSPHRASE,
        sandbox=SANDBOX
    )
    print(f"✅ CoinbaseClient initialized. SANDBOX={SANDBOX}")
except Exception as e:
    print("❌ Failed to initialize CoinbaseClient:", e)
    exit(1)

# -----------------------
# Trading function
# -----------------------
def execute_trade(symbol: str, side: str, size: float):
    """Place a market order and log the result."""
    try:
        order = client.place_order(
            product_id=symbol,
            side=side,
            order_type="market",
            size=size
        )
        print(f"{datetime.now()} ✅ {side.upper()} order placed:", order)
    except Exception as e:
        print(f"{datetime.now()} ❌ Order failed:", e)

# -----------------------
# Trading loop
# -----------------------
def main():
    print(f"🚀 Starting NIJA Trading Bot on {TRADE_SYMBOL} (interval: {TRADE_INTERVAL}s)")
    while True:
        try:
            # Example strategy: always buy (you can replace this with real logic)
            execute_trade(TRADE_SYMBOL, "buy", TRADE_SIZE)
            
            # Wait before next trade
            time.sleep(TRADE_INTERVAL)
        except KeyboardInterrupt:
            print("🛑 Bot stopped manually.")
            break
        except Exception as e:
            print("❌ Unexpected error:", e)
            time.sleep(TRADE_INTERVAL)

# -----------------------
# Entry point
# -----------------------
if __name__ == "__main__":
    main()
