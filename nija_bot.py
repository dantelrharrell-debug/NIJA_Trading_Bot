# nija_bot.py
import os
import time
from coinbase_advanced_py import Client

# -----------------------------
# 1️⃣ Load API credentials
# -----------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set. Make sure both are in your environment variables.")

# Coinbase client
try:
    cb_client = Client(API_KEY, API_SECRET)
    print("✅ Coinbase client initialized.")
except Exception as e:
    raise SystemExit(f"❌ Failed to initialize Coinbase client: {e}")

# -----------------------------
# 2️⃣ Helper functions
# -----------------------------
def get_account_balance(currency="USD"):
    try:
        accounts = cb_client.get_accounts()
        for acct in accounts:
            if acct["currency"] == currency:
                return float(acct["balance"]["amount"])
        return 0.0
    except Exception as e:
        print("❌ Error fetching accounts:", e)
        return 0.0

def place_market_order(symbol, side, size):
    try:
        order = cb_client.place_order(
            product_id=symbol,
            side=side,
            type="market",
            size=size
        )
        print(f"✅ {side.upper()} order placed for {size} {symbol}")
        return order
    except Exception as e:
        print("❌ Failed to place order:", e)
        return None

# -----------------------------
# 3️⃣ Trading loop skeleton
# -----------------------------
TRADE_SYMBOL = "BTC-USD"  # Change if needed
MIN_POSITION = 0.02       # 2% of account
MAX_POSITION = 0.10       # 10% of account

print("🚀 Starting trading loop...")

while True:
    try:
        # 1. Fetch current balance
        usd_balance = get_account_balance("USD")
        print(f"💵 USD Balance: {usd_balance}")

        # 2. Placeholder for signals (VWAP, RSI, etc.)
        # Replace this with your actual strategy
        signal = "buy"  # Example: "buy" or "sell" or None

        # 3. Calculate trade size (aggressive but safe)
        if signal == "buy":
            size = max(MIN_POSITION, min(MAX_POSITION, usd_balance * 0.05))  # Example: 5% of balance
            place_market_order(TRADE_SYMBOL, "buy", size)
        elif signal == "sell":
            # Fetch crypto balance
            crypto_balance = get_account_balance("BTC")
            size = max(MIN_POSITION, min(MAX_POSITION, crypto_balance * 0.05))
            place_market_order(TRADE_SYMBOL, "sell", size)

        # 4. Wait before next check
        time.sleep(30)  # check every 30 seconds
    except KeyboardInterrupt:
        print("🛑 Trading loop stopped by user.")
        break
    except Exception as e:
        print("❌ Trading loop error:", e)
        time.sleep(10)
