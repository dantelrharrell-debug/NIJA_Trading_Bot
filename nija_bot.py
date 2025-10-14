#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from coinbase_advanced_py import Client

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing Coinbase API_KEY or API_SECRET in .env")

# Initialize client
client = Client(API_KEY, API_SECRET)
print("🚀 Coinbase client initialized!")

# Fetch balances
try:
    balances = client.get_account_balances()
    print("💰 Balances:", balances)
except Exception as e:
    print("⚠️ Error fetching balances:", e)
