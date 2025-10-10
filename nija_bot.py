#!/usr/bin/env python3
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py:", getattr(cb, "__version__", "unknown"))
except ModuleNotFoundError as e:
    print("❌ Module 'coinbase_advanced_py' not found.", e)
    raise SystemExit(1)

try:
    client = cb.Client(API_KEY, API_SECRET)
    balances = client.get_account_balances()
    print("✅ Successfully fetched balances:")
    for b in balances:
        print(b)
except Exception as e:
    print("❌ Error fetching balances:", e)
