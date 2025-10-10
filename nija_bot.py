#!/usr/bin/env python3
import os
import sys
import time
from dotenv import load_dotenv

# --------------------------------------------
# Load environment variables
# --------------------------------------------
load_dotenv()  # Loads API_KEY, API_SECRET, DRY_RUN, SANDBOX from .env

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() in ("1", "true", "yes")
SANDBOX = os.getenv("SANDBOX", "True").lower() in ("1", "true", "yes")

if not API_KEY or not API_SECRET:
    print("⚠️ Missing API_KEY or API_SECRET in .env!")
    if not DRY_RUN:
        raise SystemExit(1)
    else:
        print("ℹ️ Continuing in DRY_RUN mode with fake keys")
        API_KEY = "FAKE_KEY"
        API_SECRET = "FAKE_SECRET"

# --------------------------------------------
# Import coinbase_advanced_py
# --------------------------------------------
try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py imported successfully")
except ModuleNotFoundError as e:
    print("❌ Module 'coinbase_advanced_py' not found:", e)
    raise SystemExit(1)

# --------------------------------------------
# Initialize Coinbase client
# --------------------------------------------
try:
    client = cb.Client(API_KEY, API_SECRET, sandbox=SANDBOX)
    print("🚀 Coinbase client initialized")
except Exception as e:
    print("❌ Error initializing Coinbase client:", e)
    raise SystemExit(1)

# --------------------------------------------
# Example: Fetch account balances
# --------------------------------------------
try:
    balances = client.get_account_balances()
    print("💰 Account balances:")
    for b in balances:
        print(f"{b['currency']}: {b['available']}")
except Exception as e:
    print("❌ Failed to fetch balances:", e)

# --------------------------------------------
# Main bot loop (placeholder)
# --------------------------------------------
try:
    while True:
        print(f"✅ Nija bot heartbeat — DRY_RUN={DRY_RUN}, SANDBOX={SANDBOX}")
        time.sleep(30)
except KeyboardInterrupt:
    print("🛑 Nija bot stopped by user")
