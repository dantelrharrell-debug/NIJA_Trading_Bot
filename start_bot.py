# start_bot.py
import os
import time
from coinbase_advanced_py import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Initialize Coinbase client
try:
    client = Client(API_KEY, API_SECRET)
    print("Coinbase client ready. Starting auto-trading loop...")
except Exception as e:
    print("Error initializing Coinbase client:", e)
    client = None

# Basic auto-trading loop (diagnostic / simple)
def auto_trade():
    if not client:
        print("Coinbase client not initialized. Exiting trading loop.")
        return

    while True:
        try:
            # Get USD balance
            usd_balance = client.get_usd_balance()
            print(f"USD Balance: {usd_balance}")

            # Example: Place a small test order if balance > 10 USD
            if usd_balance > 10:
                # Replace with a real trading symbol if desired
                test_order = client.place_order(
                    symbol="BTC-USD",
                    side="buy",
                    type="market",
                    funds="5"  # Spend 5 USD per trade
                )
                print("Placed test order:", test_order)

            # Wait 60 seconds before next check
            time.sleep(60)

        except Exception as e:
            print("Error in auto-trading loop:", e)
            time.sleep(60)

if __name__ == "__main__":
    auto_trade()
