# nija_bot_multi.py
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

try:
    cb_client = Client(API_KEY, API_SECRET)
    print("✅ Coinbase client initialized.")
except Exception as e:
    raise SystemExit(f"❌ Failed to initialize Coinbase client: {e}")

# -----------------------------
# 2️⃣ Helper functions
# -----------------------------
def get_account_balance(currency):
    try:
        accounts = cb_client.get_accounts()
        for acct in accounts:
            if acct["currency"] == currency:
                return float(acct["balance"]["amount"])
        return 0.0
    except Exception as e:
        print(f"❌ Error fetching {currency} balance:", e)
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
        print(f"❌ Failed to place {side} order for {symbol}:", e)
        return None

# -----------------------------
# 3️⃣ Multi-ticker setup
# -----------------------------
TICKERS = ["BTC-USD", "ETH-USD", "SOL-USD", "LTC-USD"]  # Add all your tickers here

MIN_POSITION = 0.02  # 2% of account
MAX_POSITION = 0.10  # 10% of account

print("🚀 Starting multi-ticker trading loop...")

while True:
    try:
        usd_balance = get_account_balance("USD")
        print(f"💵 USD Balance: {usd_balance}")

        for ticker in TICKERS:
            print(f"🔹 Checking signals for {ticker}...")

            # -----------------------------
            # 4️⃣ Placeholder for signals
            # Replace with your VWAP, RSI, or custom strategy
            # -----------------------------
            signal = None
            # Example logic: simple mock
            if ticker == "BTC-USD":
                signal = "buy"
            elif ticker == "ETH-USD":
                signal = "sell"

            # -----------------------------
            # 5️⃣ Determine trade size
            # -----------------------------
            if signal == "buy":
                size = max(MIN_POSITION, min(MAX_POSITION, usd_balance * 0.05))
                place_market_order(ticker, "buy", size)
            elif signal == "sell":
                crypto_symbol = ticker.split("-")[0]
                crypto_balance = get_account_balance(crypto_symbol)
                size = max(MIN_POSITION, min(MAX_POSITION, crypto_balance * 0.05))
                place_market_order(ticker, "sell", size)

        time.sleep(30)  # wait 30 seconds before next iteration
    except KeyboardInterrupt:
        print("🛑 Trading loop stopped by user.")
        break
    except Exception as e:
        print("❌ Trading loop error:", e)
        time.sleep(10)
