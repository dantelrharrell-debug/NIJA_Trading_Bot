import os
from coinbase.rest import RESTClient

# 🔐 Load Coinbase credentials
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET")

# ✅ Create Coinbase client using API_KEY + API_SECRET
try:
    client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
    print("✅ RESTClient created using API_KEY + API_SECRET")
except Exception as e:
    raise SystemExit(f"❌ Failed to start Coinbase client: {type(e).__name__} {e}")

# Example: check account balances
try:
    balances = client.get_account_balances()
    print("💰 Account balances:", balances)
except Exception as e:
    print("❌ Failed to fetch balances:", type(e).__name__, e)

# --- Your bot logic goes below ---
# e.g., trading functions, webhooks, loops, etc.
