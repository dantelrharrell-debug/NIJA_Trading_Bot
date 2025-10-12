import sys
import site
import os
import coinbase_advanced_py as cb

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

# ------------------------
# VALIDATION
# ------------------------
if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set. Add them to your environment variables.")

# ------------------------
# INITIALIZE CLIENT
# ------------------------
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("✅ Coinbase client initialized using API_KEY + API_SECRET")
except Exception as e:
    raise SystemExit(f"❌ Failed to initialize Coinbase client: {e}")

# ------------------------
# CHECK ACCOUNTS
# ------------------------
try:
    accounts = client.get_account_balances()
    print("💰 Accounts snapshot:", accounts)
except Exception as e:
    print(f"⚠️ get_accounts() error: {e}")

# ------------------------
# LIVE TRADING INFO
# ------------------------
print(f"LIVE_TRADING: {LIVE_TRADING}")
print(f"Service running on PORT: {PORT}")
