import os
import time
import pandas as pd
import coinbase_advanced_py as cb
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise ValueError("❌ API_KEY or API_SECRET missing")

client = cb.Client(API_KEY, API_SECRET)
print("🚀 Coinbase client initialized")

# Example: fetch account balances
balances = client.get_account_balances()
print("Balances:", balances)
