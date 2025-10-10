#!/usr/bin/env python3
import os
import coinbase_advanced_py as cb

# -----------------------------
# Load API keys from environment
# -----------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() == "true"

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET environment variables")

# -----------------------------
# Initialize Coinbase client
# -----------------------------
client = cb.Client(API_KEY, API_SECRET)
print("🚀 Nija Trading Bot initialized")

# -----------------------------
# Example: check balances
# -----------------------------
try:
    balances = client.get_account_balances()
    print("💰 Account balances:", balances)
except Exception as e:
    print("❌ Failed to fetch balances:", e)

# -----------------------------
# Bot logic placeholder
# -----------------------------
# Example:
# client.place_order(
#     product_id="BTC-USD",
#     side="buy",
#     order_type="market",
#     size="0.001"
# )
