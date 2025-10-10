#!/usr/bin/env python3
import os
import sys

# -----------------------------
# 1️⃣ Import coinbase_advanced_py
# -----------------------------
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except ModuleNotFoundError:
    raise SystemExit("❌ coinbase_advanced_py not found. Make sure requirements.txt includes it.")

# -----------------------------
# 2️⃣ Load API keys from environment
# -----------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() == "true"

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET environment variables")

# -----------------------------
# 3️⃣ Initialize Coinbase client
# -----------------------------
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("🚀 Nija Trading Bot initialized")
except AttributeError:
    raise SystemExit("❌ coinbase_advanced_py has no attribute 'Client'. Check your version.")

# -----------------------------
# 4️⃣ Example: check balances
# -----------------------------
try:
    balances = client.get_account_balances()
    print("💰 Account balances:", balances)
except Exception as e:
    print("❌ Failed to fetch balances:", e)

# -----------------------------
# 5️⃣ Bot logic placeholder
# -----------------------------
# Example: client.place_order(...)
