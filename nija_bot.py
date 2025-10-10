#!/usr/bin/env python3
import sys
import os

# Add vendor folder to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vendor"))

import coinbase_advanced_py as cb
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
DRY_RUN = os.getenv("DRY_RUN", "True").lower() == "true"

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET")

# Initialize Coinbase client
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("🚀 Nija Trading Bot initialized")
except AttributeError:
    raise SystemExit("❌ coinbase_advanced_py has no attribute 'Client'")

# Example: check balances
try:
    balances = client.get_account_balances()
    print("💰 Balances:", balances)
except Exception as e:
    print("❌ Failed to fetch balances:", e)
