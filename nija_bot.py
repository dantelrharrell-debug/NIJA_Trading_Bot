import os
import coinbase_advanced_py as cb
import time

# --- Load environment variables ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
PASSPHRASE = os.getenv("PASSPHRASE")  # Optional, only if your Coinbase API requires it

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set")

# --- Initialize Coinbase client ---
try:
    client = cb.Client(API_KEY, API_SECRET, passphrase=PASSPHRASE)
    print("✅ Coinbase client started successfully!")
except Exception as e:
    raise SystemExit(f"❌ Failed to start Coinbase client: {e}")

# --- Example: check balances ---
try:
    balances = client.get_account_balances()
    print("💰 Current balances:")
    for account in balances:
        print(f"{account['currency']}: {account['balance']}")
except Exception as e:
    print("❌ Failed to fetch balances:", e)

# --- Optional: live trading loop ---
# while True:
#     # Here you can add your trading logic
#     time.sleep(60)
