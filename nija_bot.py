import os
import time
import traceback

# ------------------------
# ENVIRONMENT VARIABLES
# ------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
LIVE_TRADING = os.getenv("LIVE_TRADING", "False").lower() == "true"

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set.")

print("✅ Environment variables loaded")
print(f"LIVE_TRADING: {LIVE_TRADING}")

# ------------------------
# INITIALIZE COINBASE CLIENT
# ------------------------
def init_client():
    while True:
        try:
            import coinbase_advanced_py as cb
            client = cb.Client(API_KEY, API_SECRET)
            print("✅ Coinbase client initialized")
            return client
        except ModuleNotFoundError:
            print("⚠️ coinbase_advanced_py not installed. Retrying in 10s...")
        except Exception as e:
            print(f"⚠️ Failed to initialize client: {e}. Retrying in 10s...")
        time.sleep(10)

# ------------------------
# CHECK ACCOUNTS
# ------------------------
def check_accounts(client):
    try:
        accounts = client.get_account_balances()
        print("💰 Accounts snapshot:", accounts)
    except Exception as e:
        print(f"⚠️ Error fetching accounts: {e}")

# ------------------------
# BOT LOOP
# ------------------------
def run_bot(client):
    print("✅ Worker is running")
    while True:
        try:
            btc_price = client.get_price("BTC-USD")
            print("📈 Current BTC price:", btc_price)
            # TODO: Add your trading logic here
        except Exception as e:
            print(f"⚠️ Error fetching BTC price: {e}")
        time.sleep(10)  # repeat every 10 seconds

# ------------------------
# SELF-HEALING LOOP
# ------------------------
while True:
    try:
        client = init_client()
        check_accounts(client)
        run_bot(client)
    except Exception:
        print("❌ Bot crashed unexpectedly. Restarting in 5s...")
        traceback.print_exc()
        time.sleep(5)
