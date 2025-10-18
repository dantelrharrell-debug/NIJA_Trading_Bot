import os
import coinbase_advanced_py as cb

# Load your API keys from environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise ValueError("Missing Coinbase API_KEY or API_SECRET")

client = cb.Client(API_KEY, API_SECRET)

# Test parameters
symbol = "BTC-USD"  # Can change to any supported pair
test_amount = 1     # $1 for testing
side = "buy"        # "buy" or "sell"

try:
    # Create a test order
    order = client.place_order(
        symbol=symbol,
        side=side,
        type="market",
        funds=test_amount  # this is USD value
    )
    print("✅ Test order executed successfully:")
    print(order)
except Exception as e:
    print("❌ Test order failed:")
    print(e)
    
