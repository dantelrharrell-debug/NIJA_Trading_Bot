#!/usr/bin/env python3
import os
import sys

print("✅ Python executable:", sys.executable)
print("✅ sys.path:", sys.path)

# Test importing coinbase_advanced_py
try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py imported successfully!")
except ModuleNotFoundError:
    print("❌ coinbase_advanced_py NOT found")
    sys.exit(1)

# Load Coinbase API credentials from environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    print("❌ API_KEY or API_SECRET not set")
    sys.exit(1)

# Create Coinbase client
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("✅ Coinbase client created successfully!")
except Exception as e:
    print(f"❌ Failed to create Coinbase client: {e}")
    sys.exit(1)

# Optional: check account balances
try:
    balances = client.get_account_balances()
    print("✅ Coinbase balances fetched successfully:")
    print(balances)
except Exception as e:
    print(f"❌ Failed to fetch balances: {e}")
