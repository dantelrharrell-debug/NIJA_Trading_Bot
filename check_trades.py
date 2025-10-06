import coinbase_advanced_py as cb
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

client = cb.Client(API_KEY, API_SECRET)

# Fetch recent trades
recent_trades = client.get_recent_trades()  # or similar method in coinbase_advanced_py
print("Recent trades executed by the bot:")
print(recent_trades)
