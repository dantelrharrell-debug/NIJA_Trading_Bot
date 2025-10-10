#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import coinbase_advanced_py as cb

# Load .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Initialize client
client = cb.Client(API_KEY, API_SECRET)

# Example fetch accounts
balances = client.get_account_balances()
print(balances)
