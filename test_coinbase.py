import os
import coinbase_advanced_py as cb

# 1️⃣ Get API keys from Render environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set in Render environment!")

# 2️⃣ Connect to Coinbase
client = cb.Client(API_KEY, API_SECRET)

# 3️⃣ Check Spot account balances
try:
    spot_accounts = client.get_account_balances()
    print("✅ Spot connection works! Spot balances:")
    for account in spot_accounts:
        print(f" - {account['currency']}: {account['balance']}")
except Exception as e:
    print("❌ Spot connection failed:", e)

# 4️⃣ Check Futures account balances
try:
    futures_accounts = client.get_futures_account_balances()
    print("\n✅ Futures connection works! Futures balances:")
    for account in futures_accounts:
        print(f" - {account['currency']}: {account['balance']}")
except Exception as e:
    print("❌ Futures connection failed:", e)

# 5️⃣ Optional: fetch last 5 orders to confirm trades are executing
try:
    recent_spot_orders = client.get_recent_orders(product_id="BTC-USD", limit=5)
    recent_futures_orders = client.get_recent_futures_orders(product_id="BTC-USD-PERP", limit=5)
    print("\n📈 Recent Spot Orders:", recent_spot_orders)
    print("\n📈 Recent Futures Orders:", recent_futures_orders)
except Exception as e:
    print("❌ Failed to fetch recent orders:", e)
