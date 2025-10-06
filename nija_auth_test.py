import os
import coinbase_advanced_py as cb

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise ValueError("Missing Coinbase API_KEY or API_SECRET")

client = cb.Client(API_KEY, API_SECRET)
print("✅ Authentication successful")

accounts = client.get_accounts()
print(accounts)
