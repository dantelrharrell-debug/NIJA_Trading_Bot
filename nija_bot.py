# nija_bot.py

import os
import coinbase_advanced_py as cb

# --- Initialize Coinbase client with API_KEY + API_SECRET ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "False").lower() == "true"

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET environment variables")

client = cb.Client(API_KEY, API_SECRET)

# --- Example: fetch balances ---
try:
    balances = client.get_account_balances()
    print("✅ Account balances:")
    for account in balances:
        print(f" - {account['currency']}: {account['balance']}")
except Exception as e:
    print(f"❌ Failed to fetch balances: {e}")

# --- Example trading logic ---
def example_trade():
    if DRY_RUN:
        print("ℹ️ DRY_RUN: Skipping live trade")
        return
    try:
        print("ℹ️ Example trade executed (replace with real logic)")
        # Add your buy/sell calls here using `client`
    except Exception as e:
        print(f"❌ Trade failed: {e}")

# Run example trade
example_trade()
