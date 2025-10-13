# main.py
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
client = cb.Client(API_KEY, API_SECRET)

print("🚀 Coinbase bot started")

# Example: check balances
try:
    balances = client.get_account_balances()
    print("✅ Balances:", balances)
except Exception as e:
    print("❌ Failed to fetch balances:", e)

# TODO: Add your trading logic here
