#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set in environment variables")

# Correct import for Coinbase Advanced Py
from coinbase_advanced_py.client import Client

# Initialize client
client = Client(API_KEY, API_SECRET)

print("🚀 NIJA BOT started successfully!")

# Example: Check account balances to verify connectivity
try:
    balances = client.get_account_balances()
    print("✅ Coinbase balances fetched successfully:")
    print(balances)
except Exception as e:
    print("❌ Error connecting to Coinbase:")
    print(e)
    sys.exit(1)

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
