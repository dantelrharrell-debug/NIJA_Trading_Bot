import os
from coinbase.wallet.client import Client

# Load API keys from environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

client = Client(API_KEY, API_SECRET)

# Try a tiny test buy to check connectivity
try:
    btc_account = client.get_account('BTC-USD')
    test_order = btc_account.buy(amount='0.000001', currency='BTC')  # Tiny test buy
    print("✅ Test order executed:", test_order)
except Exception as e:
    print("❌ Test order failed:", e)
