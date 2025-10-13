# main.py (near the top, after .env/API keys loaded)
import sys
import pkgutil
import importlib.util

# Preferred: import the library correctly
try:
    # Example: import the REST client class used by the SDK
    from coinbase.rest import RESTClient
    print("✅ coinbase (coinbase-advanced-py) import successful: from coinbase.rest import RESTClient")
except ModuleNotFoundError:
    print("❌ coinbase NOT found (package may not be installed into this Python interpreter)")
    print("Python executable:", sys.executable)
    print("sys.path (sample):", sys.path[:6])
    # Exit if you want the deploy to fail early when missing
    # import sys; sys.exit(1)

# (Optional) lightweight check if you want to keep the original style:
try:
    import coinbase
    print("✅ coinbase import OK")
except ModuleNotFoundError:
    print("❌ coinbase import failed")

# main.py (near the top, after loading .env / API keys)
import importlib.util
import pkgutil
import sys

# quick, non-fatal import check
try:
    # correct import for the official SDK:
    from coinbase.rest import RESTClient
    print("✅ coinbase (coinbase-advanced-py package) import successful: from coinbase.rest import RESTClient")
except ModuleNotFoundError:
    print("❌ coinbase NOT found (the package 'coinbase-advanced-py' may be installed under a different name or not installed into this Python interpreter)")

# Extra diagnostics (helpful in deploy logs)
print("Python executable:", sys.executable)
print("sys.path (first entries):", sys.path[:6])
print("pkgutil.find_loader('coinbase'):", pkgutil.find_loader("coinbase"))
print("importlib.util.find_spec('coinbase'):", importlib.util.find_spec("coinbase"))

import sys
print(sys.executable)

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
