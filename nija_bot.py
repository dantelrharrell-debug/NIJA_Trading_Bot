import sys
import site
import os
import time
import traceback

# ------------------------
# GREEN CHECKS: Python environment
# ------------------------
print("🐍 Python executable:", sys.executable)
print("📂 Python site-packages:", site.getsitepackages())
print("✅ sys.path:", sys.path)

# ------------------------
# ENVIRONMENT VARIABLES
# ------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
LIVE_TRADING = os.getenv("LIVE_TRADING", "False").lower() == "true"

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set. Add them to your environment variables.")

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
# FUNCTION TO RUN BOT LOOP
# ------------------------
def run_bot(client):
    print("✅ Worker is ready and running")
    while True:
        try:
            btc_price = client.get_price("BTC-USD")
            print("📈 Current BTC price:", btc_price)
        except Exception as e:
            print(f"⚠️ Error fetching BTC price: {e}")
        time.sleep(10)  # adjust frequency for your strategy

# ------------------------
# SELF-HEALING MAIN LOOP
# ------------------------
while True:
    try:
        client = init_coinbase_client()

        # GREEN CHECK: accounts snapshot
        try:
            accounts = client.get_account_balances()
            print("💰 Accounts snapshot:", accounts)
        except Exception as e:
            print(f"⚠️ get_account_balances() error: {e}")

        run_bot(client)

    except Exception:
        print("❌ Bot crashed unexpectedly. Restarting in 5s...")
        traceback.print_exc()
        time.sleep(5)
