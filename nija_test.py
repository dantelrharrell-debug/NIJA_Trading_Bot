import sys
print("Python executable:", sys.executable)
print("sys.path:", sys.path)

try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py import successful!")
except ModuleNotFoundError:
    print("❌ coinbase_advanced_py NOT found")

# nija_bot_test.py

import os
import sys

print("🔹 Python executable:", sys.executable)
print("🔹 sys.path:", sys.path)

# ------------------ Package Imports ------------------
try:
    import coinbase_advanced_py as cb
    import flask
    import pandas as pd
    print("✅ All packages imported successfully!")
except ModuleNotFoundError as e:
    print(f"❌ Package import failed: {e}")
    sys.exit(1)

# ------------------ Load API Credentials ------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    print("⚠️ python-dotenv not installed. Skipping .env load")

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    print("❌ API_KEY or API_SECRET not set in environment!")
    sys.exit(1)

# ------------------ Initialize Coinbase Client ------------------
try:
    client = cb.Client(API_KEY, API_SECRET)
    balances = client.get_account_balances()
    print("💰 Coinbase balances:")
    for acct, bal in balances.items():
        print(f"  {acct}: {bal}")
except Exception as e:
    print(f"❌ Coinbase API test failed: {e}")
    sys.exit(1)

print("🎉 Environment & Coinbase API test passed successfully!")
