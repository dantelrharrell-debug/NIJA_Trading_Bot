import os
from time import sleep
import coinbase_advanced_py as cb

# ✅ Environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SANDBOX = True  # Always True for testing since you only have 1 simulation
TRADE_SYMBOLS = ["BTC-USD", "ETH-USD", "LTC-USD"]  # Add all your trade symbols here
TRADE_AMOUNT = 10
SLEEP_INTERVAL = 10  # seconds

# Check keys
if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set in environment variables.")

# Initialize Coinbase client in sandbox mode
client = cb.Client(API_KEY, API_SECRET, sandbox=SANDBOX)
print("🚀 Coinbase sandbox client initialized")

# Fetch balances once to confirm connection
try:
    balances = client.get_account_balances()
    print("💰 Balances:", balances)
except Exception as e:
    print("❌ Error fetching balances:", e)
    exit(1)

# Minimal trading loop for testing
while True:
    for symbol in TRADE_SYMBOLS:
        try:
            price = client.get_product_price(symbol)
            print(f"📈 Current price of {symbol}: {price}")
            # Example trade logic (uncomment to execute)
            # client.place_market_order(symbol, "buy", TRADE_AMOUNT)
        except Exception as e:
            print(f"❌ Trading error for {symbol}:", e)

    sleep(SLEEP_INTERVAL)
