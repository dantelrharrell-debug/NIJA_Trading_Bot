import os
from time import sleep
import coinbase_advanced_py as cb

# ✅ Grab API keys from environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SANDBOX = os.getenv("SANDBOX", "True") == "True"

# Trade settings
TRADE_SYMBOLS = os.getenv("TRADE_SYMBOLS", "BTC-USD,ETH-USD,LTC-USD").split(",")
TRADE_AMOUNT = float(os.getenv("TRADE_AMOUNT", "10"))
SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", "10"))

# Check keys
if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set in environment variables.")

# Initialize Coinbase client
client = cb.Client(API_KEY, API_SECRET, sandbox=SANDBOX)
print("✅ Coinbase client initialized")

# Example: print balances
try:
    balances = client.get_account_balances()
    print("💰 Balances:", balances)
except Exception as e:
    print("❌ Error fetching balances:", e)

# Trading loop (replace with your logic)
while True:
    for symbol in TRADE_SYMBOLS:
        try:
            price = client.get_product_price(symbol)
            print(f"📈 Current price of {symbol}: {price}")

            # Example: place market buy order (uncomment to activate)
            # client.place_market_order(symbol, "buy", TRADE_AMOUNT)

        except Exception as e:
            print(f"❌ Trading error for {symbol}:", e)

    sleep(SLEEP_INTERVAL)
