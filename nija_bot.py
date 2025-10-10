import sys
import os

# Add the vendor folder (must be committed to GitHub)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vendor"))

import coinbase_advanced_py as cb
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET")

client = cb.Client(API_KEY, API_SECRET)
print("🚀 Nija Trading Bot initialized")

balances = client.get_account_balances()
print("💰 Balances:", balances)
