import os
import coinbase_advanced_py as cb
from time import sleep

# ✅ Grab API keys from Render environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SANDBOX = os.getenv("SANDBOX", "True") == "True"
TRADE_SYMBOL = os.getenv("TRADE_SYMBOL", "BTC-USD")
TRADE_AMOUNT = float(os.getenv("TRADE_AMOUNT", "10"))
SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", "10"))

# Check keys
if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set in environment variables.")

# Initialize Coinbase client
client = cb.Client(API_KEY, API_SECRET, sandbox=SANDBOX)
print("🚀 Coinbase client initialized")

# Example: print balances
try:
    balances = client.get_account_balances()
    print("💰 Balances:", balances)
except Exception as e:
    print("❌ Error fetching balances:", e)

# Example trading loop (replace with your logic)
while True:
    try:
        price = client.get_product_price(TRADE_SYMBOL)
        print(f"📈 Current price of {TRADE_SYMBOL}: {price}")

        # Place order logic here
        # Example: client.place_market_order(TRADE_SYMBOL, "buy", TRADE_AMOUNT)
        
    except Exception as e:
        print("❌ Trading error:", e)

    sleep(SLEEP_INTERVAL)
