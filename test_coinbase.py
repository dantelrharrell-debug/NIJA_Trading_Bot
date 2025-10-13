import os
from coinbase_advanced_py import Client
from dotenv import load_dotenv

# Load your .env variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    print("❌ Missing API_KEY or API_SECRET in .env")
    exit(1)

try:
    client = Client(API_KEY, API_SECRET)
    accounts = client.get_accounts()  # fetch account info
    print("✅ Coinbase Advanced module imported successfully!")
    print("Accounts info (first 2 only for safety):")
    for acc in accounts[:2]:
        print(acc)
except Exception as e:
    print("❌ Error connecting to Coinbase:")
    print(e)
