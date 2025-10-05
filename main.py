import os
import time
import coinbase_advanced_py as cb

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise ValueError("Missing Coinbase API_KEY or API_SECRET")

client = cb.Client(API_KEY, API_SECRET)

print("🚀 Trading bot started.")

while True:
    try:
        balances = client.get_account_balances()
        print(f"Balances: {balances}")
        # TODO: add trading logic here
    except Exception as e:
        print(f"⚠️ Trading error: {e}")
    time.sleep(10)

import os
from coinbase.wallet.client import Client

# Load your API keys from environment
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

client = Client(API_KEY, API_SECRET)

# Get BTC account
btc_account = client.get_account('BTC-USD')

# Test order (very tiny amount)
try:
    test_order = btc_account.buy(amount='0.000001', currency='BTC')  # Tiny amount to avoid risk
    print("✅ Test order executed:")
    print(test_order)
except Exception as e:
    print("❌ Test order failed:")
    print(e)
