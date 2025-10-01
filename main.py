import os
from coinbase.wallet.client import Client  # Using the standard Coinbase package
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise ValueError("API_KEY or API_SECRET not found. Please set them in your .env file.")

# Initialize Coinbase client
client = Client(API_KEY, API_SECRET)
print("✅ Coinbase client initialized successfully!")

# Example: Get account info
try:
    accounts = client.get_accounts()
    print(f"Found {len(accounts.data)} account(s).")
    for account in accounts.data:
        print(f"{account.name}: {account.balance.amount} {account.balance.currency}")
except Exception as e:
    print(f"Error fetching accounts: {e}")

# Add your trading logic here
# For example, you can call client.buy(), client.sell(), client.get_buy_price(), etc.

# Keep the script running (if needed)
import time
while True:
    # Placeholder for real trading loop
    time.sleep(60)
