import os
import coinbase_advanced_py as cb
from time import sleep

# ✅ Environment variables from Render
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SANDBOX = os.getenv("SANDBOX", "True") == "True"
TRADE_SYMBOLS = os.getenv("TRADE_SYMBOLS", "BTC-USD,ETH-USD").split(",")
TRADE_AMOUNT = float(os.getenv("TRADE_AMOUNT", "10"))
SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", "10"))

# Check keys
if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set in environment variables.")

# Initialize Coinbase client
client = cb.Client(API_KEY, API_SECRET, sandbox=SANDBOX)
print("🚀 Coinbase client initialized")

# Print balances
try:
    balances = client.get_account_balances()
    print("💰 Balances:", balances)
except Exception as e:
    print("❌ Error fetching balances:", e)

# Main trading loop
while True:
    for symbol in TRADE_SYMBOLS:
        try:
            price = client.get_product_price(symbol)
            print(f"📈 Current price of {symbol}: {price}")

            # TODO: Implement stop loss / take profit logic here
            # Example: client.place_market_order(symbol, "buy", TRADE_AMOUNT)
            
        except Exception as e:
            print(f"❌ Trading error for {symbol}:", e)
    sleep(SLEEP_INTERVAL)
