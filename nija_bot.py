#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# -----------------------------------------
# 1️⃣ Load environment variables
# -----------------------------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# -----------------------------------------
# 2️⃣ Import coinbase_advanced_py directly from pip-installed packages
# -----------------------------------------
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except ModuleNotFoundError as e:
    print("❌ Module 'coinbase_advanced_py' not found. Did you run 'pip install -r requirements.txt'?", e)
    raise SystemExit(1)

# -----------------------------------------
# 3️⃣ Initialize client and fetch balances
# -----------------------------------------
try:
    client = cb.Client(API_KEY, API_SECRET)
    balances = client.get_account_balances()
    print("✅ Successfully fetched account balances:")
    for b in balances:
        print(b)
except Exception as e:
    print("❌ Error fetching balances:", e)
