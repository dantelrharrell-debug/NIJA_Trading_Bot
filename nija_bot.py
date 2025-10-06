#!/usr/bin/env python3
# nija_bot.py

import os
from dotenv import load_dotenv
import coinbase_advanced_py as cb
import time

# =============================
# Load API keys from .env
# =============================
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise ValueError("❌ API_KEY or API_SECRET missing")

# =============================
# Initialize Coinbase client
# =============================
client = cb.Client(API_KEY, API_SECRET)
print("✅ Coinbase client initialized")

# =============================
# Helper function: check balances
# =============================
def check_balances():
    balances = client.get_account_balances()
    print("💰 Current balances:")
    for symbol, info in balances.items():
        print(f"{symbol}: {info['available']} available, {info['hold']} hold")
    return balances

# =============================
# Example: main trading loop
# =============================
def main():
    print("🚀 Starting trading bot loop...")
    while True:
        try:
            balances = check_balances()

            # =============================
            # PLACE YOUR TRADING LOGIC HERE
            # =============================
            # Example placeholder:
            # if some_condition:
            #     client.place_order(symbol="BTC-USD", side="buy", type="market", size=0.01)

            # Wait before next iteration (adjust for your strategy)
            time.sleep(10)  # checks balances every 10 seconds

        except Exception as e:
            print("❌ Error:", e)
            time.sleep(5)

# =============================
# Run the bot
# =============================
if __name__ == "__main__":
    main()
