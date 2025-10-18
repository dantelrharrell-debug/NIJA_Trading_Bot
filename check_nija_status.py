import os
from dotenv import load_dotenv
import coinbase_advanced_py as cb
import time

# Load API keys from .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET in .env")

# Initialize Coinbase client
client = cb.Client(API_KEY, API_SECRET)

def get_balances():
    try:
        balances = client.get_account_balances()
        print("💰 Current Account Balances:")
        for symbol, info in balances.items():
            print(f"{symbol}: {info['available']} available, {info['hold']} on hold")
    except Exception as e:
        print(f"⚠️ Error fetching balances: {e}")

def get_recent_trades():
    try:
        trades = client.get_recent_trades()  # Adjust if coinbase_advanced_py method differs
        if trades:
            print("\n📈 Recent Trades:")
            for t in trades[:10]:  # show latest 10 trades
                print(f"{t['time']} | {t['side']} {t['size']} {t['symbol']} at {t['price']}")
        else:
            print("\nℹ️ No recent trades found.")
    except Exception as e:
        print(f"⚠️ Error fetching recent trades: {e}")

def main():
    print("🚀 Checking NIJA Trading Bot status...\n")
    get_balances()
    get_recent_trades()

if __name__ == "__main__":
    main()
