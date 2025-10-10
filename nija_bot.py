#!/usr/bin/env python3
import os
import coinbase_advanced_py as cb

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() == "true"

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET environment variables")

client = cb.Client(API_KEY, API_SECRET)
print("🚀 Nija Trading Bot initialized")

try:
    balances = client.get_account_balances()
    print("💰 Account balances:", balances)
except Exception as e:
    print("❌ Failed to fetch balances:", e)
