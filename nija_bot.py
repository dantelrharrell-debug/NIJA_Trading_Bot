import os
from dotenv import load_dotenv
import coinbase_advanced_py as cb
import time

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API credentials. Set API_KEY and API_SECRET in Render dashboard.")

client = cb.Client(API_KEY, API_SECRET)

print("✅ NIJA Bot connected to Coinbase Advanced!")

while True:
    try:
        balances = client.get_account_balances()
        print("📊 Current balances:", balances)
        time.sleep(15)
    except Exception as e:
        print("⚠️ Error:", e)
        time.sleep(30)
