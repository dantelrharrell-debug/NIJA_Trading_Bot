#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET in environment variables")

try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    raise SystemExit("❌ coinbase_advanced_py not installed. Check requirements.txt")

# Initialize client
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("✅ Coinbase client created")
except Exception as e:
    raise SystemExit(f"❌ Failed to initialize Coinbase client: {e}")

# Example: check balances
try:
    balances = client.get_account_balances()
    print("✅ Balances:", balances)
except Exception as e:
    print("❌ Failed to fetch balances:", e)

# TODO: Add your trading logic here
