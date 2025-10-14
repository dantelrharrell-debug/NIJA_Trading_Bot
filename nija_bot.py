#!/usr/bin/env python3
import os
import sys
import json
import traceback
import coinbase_advanced_py as cb
from dotenv import load_dotenv

# Load environment variables from .env (if it exists)
load_dotenv()

# ----------------- Config -----------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ ERROR: API_KEY or API_SECRET not set in environment.")

# ----------------- Initialize client -----------------
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("✅ Coinbase Advanced client initialized successfully!")
except Exception as e:
    print("❌ Failed to initialize Coinbase client:")
    print(str(e))
    sys.exit(1)

# ----------------- Example: Get account balances -----------------
try:
    balances = client.get_account_balances()
    print("💰 Current balances:")
    print(json.dumps(balances, indent=2))
except Exception as e:
    print("❌ Failed to fetch balances:")
    traceback.print_exc()

# ----------------- Main bot logic placeholder -----------------
def main():
    print("🚀 Nija bot is running...")
    # Add your trading logic here
    # Example: client.create_order(...) or client.get_market_data(...)
    pass

if __name__ == "__main__":
    main()
