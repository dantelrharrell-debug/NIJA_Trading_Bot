#!/usr/bin/env python3
import os
import time
import traceback

# ✅ Load Coinbase client
try:
    from coinbase_advanced_py import Client
except ModuleNotFoundError:
    print("❌ coinbase_advanced_py not installed or not found")
    raise

# Load environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set in environment variables")

# Initialize Coinbase client
client = Client(API_KEY, API_SECRET)
print("✅ Coinbase client initialized")

# Optional: function to fetch and print balances
def check_balances():
    try:
        balances = client.get_account_balances()
        print("💰 Balances:", balances)
    except Exception as e:
        print("❌ Error fetching balances:", e)
        traceback.print_exc()

# Optional: function to execute trades
def execute_trades():
    try:
        # Example: replace with your bot logic
        print("🔄 Executing trade logic...")
    except Exception as e:
        print("❌ Trade execution error:", e)
        traceback.print_exc()

# ---------------------- MAIN LOOP ----------------------
print("🚀 Bot started and running")
while True:
    try:
        check_balances()
        execute_trades()
        # Sleep between iterations to avoid API rate limits
        time.sleep(5)  # adjust as needed
    except KeyboardInterrupt:
        print("🛑 Bot stopped manually")
        break
    except Exception as main_e:
        print("❌ Unexpected error in main loop:", main_e)
        traceback.print_exc()
        time.sleep(5)
