import sys
sys.path.insert(0, "vendor")  # Add vendor folder to module path

import coinbase_advanced_py as cb
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vendor"))

import coinbase_advanced_py as cb
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
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("🚀 Nija Trading Bot initialized")
except AttributeError:
    raise SystemExit("❌ coinbase_advanced_py has no attribute 'Client'. Check your version.")

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
# if not DRY_RUN:
#     client.place_order(product_id="BTC-USD", side="buy", price="30000", size="0.001")
