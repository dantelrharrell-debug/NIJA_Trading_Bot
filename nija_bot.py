#!/usr/bin/env python3
import os
import time
from coinbase.rest import RESTClient

# ===============================
# 🔐 Load Coinbase credentials
# ===============================
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET environment variables")

# ===============================
# ✅ Initialize Coinbase client
# ===============================
try:
    client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
    print("✅ RESTClient created using API_KEY + API_SECRET")
except Exception as e:
    raise SystemExit(f"❌ Failed to start Coinbase client: {type(e).__name__} {e}")

# ===============================
# Example: Fetch account balances
# ===============================
def get_balances():
    try:
        balances = client.get_account_balances()
        print("💰 Account balances:")
        for account in balances:
            print(f"{account['currency']}: {account['available']}")
        return balances
    except Exception as e:
        print("❌ Failed to fetch balances:", type(e).__name__, e)
        return []

# ===============================
# Your trading logic goes here
# ===============================
def main_loop():
    print("🚀 Nija bot running...")
    while True:
        # Example: check balances every 30 seconds
        get_balances()
        # TODO: Replace with your VWAP / RSI / trading strategy logic
        time.sleep(30)  # adjust as needed

# ===============================
# Start bot
# ===============================
if __name__ == "__main__":
    main_loop()
