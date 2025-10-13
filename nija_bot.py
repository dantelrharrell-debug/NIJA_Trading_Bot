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
    raise SystemExit("❌ API_KEY or API_SECRET not set. Add them to your environment variables.")

print("✅ Environment variables loaded")
print(f"LIVE_TRADING: {LIVE_TRADING}")

# ------------------------
# FUNCTION TO INIT COINBASE CLIENT
# ------------------------
def init_coinbase_client():
    while True:
        try:
            import coinbase_advanced_py as cb
            client = cb.Client(API_KEY, API_SECRET)
            print("✅ Coinbase client initialized")
            return client
        except ModuleNotFoundError:
            print("⚠️ coinbase_advanced_py not found. Retrying in 10s...")
        except Exception as e:
            print(f"⚠️ Failed to initialize Coinbase client: {e}. Retrying in 10s...")
        time.sleep(10)

# ------------------------
# FUNCTION TO FETCH ACCOUNTS
# ------------------------
def check_accounts(client):
    try:
        accounts = client.get_account_balances()
        print("💰 Accounts snapshot:", accounts)
    except Exception as e:
        print(f"⚠️ get_account_balances() error: {e}")

# ------------------------
# MAIN BOT LOOP
# ------------------------
def run_bot(client):
    print("✅ Worker is ready and running")
    while True:
        try:
            btc_price = client.get_price("BTC-USD")
            print("📈 Current BTC price:", btc_price)
        except Exception as e:
            print(f"⚠️ Error fetching BTC price: {e}")
        time.sleep(10)  # adjust interval to your strategy

# ------------------------
# SELF-HEALING LOOP
# ------------------------
while True:
    try:
        client = init_coinbase_client()
        check_accounts(client)
        run_bot(client)
    except Exception:
        print("❌ Bot crashed unexpectedly. Restarting in 5s...")
        traceback.print_exc()
        time.sleep(5)
