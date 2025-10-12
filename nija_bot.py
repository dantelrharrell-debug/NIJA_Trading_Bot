import sys
import site
import os
import time

print("🐍 Python executable:", sys.executable)
print("📂 Python site-packages:", site.getsitepackages())
print("✅ sys.path:", sys.path)

# ------------------------
# ENVIRONMENT VARIABLES
# ------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
LIVE_TRADING = os.getenv("LIVE_TRADING", "False").lower() == "true"
PORT = int(os.getenv("PORT", 10000))

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set. Add them to your environment variables.")

# ------------------------
# HELPER FUNCTION TO INIT CLIENT
# ------------------------
def init_coinbase_client():
    try:
        import coinbase_advanced_py as cb
        client = cb.Client(API_KEY, API_SECRET)
        print("✅ Coinbase client initialized")
        return client
    except ModuleNotFoundError:
        print("⚠️ coinbase_advanced_py module not found. Retrying in 10s...")
    except Exception as e:
        print(f"⚠️ Failed to initialize Coinbase client: {e}. Retrying in 10s...")
    return None

# ------------------------
# AUTO-RETRY LOOP
# ------------------------
client = None
while client is None:
    client = init_coinbase_client()
    if client is None:
        time.sleep(10)

# ------------------------
# CHECK ACCOUNTS
# ------------------------
try:
    accounts = client.get_account_balances()
    print("💰 Accounts snapshot:", accounts)
except Exception as e:
    print(f"⚠️ get_account_balances() error: {e}")

# ------------------------
# LIVE TRADING INFO
# ------------------------
print(f"LIVE_TRADING: {LIVE_TRADING}")
print(f"Service running on PORT: {PORT}")

# ------------------------
# EXAMPLE BOT LOOP (replace with your trading logic)
# ------------------------
try:
    while True:
        try:
            btc_price = client.get_price("BTC-USD")
            print("📈 Current BTC price:", btc_price)
        except Exception as e:
            print(f"⚠️ Error fetching BTC price: {e}")
        time.sleep(10)  # Fetch every 10 seconds (adjust to your strategy)
except KeyboardInterrupt:
    print("🛑 Bot stopped manually")
