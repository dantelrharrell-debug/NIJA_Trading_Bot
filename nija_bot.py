rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

import os
import coinbase_advanced_py as cb

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

# ------------------------
# PLACE YOUR BOT LOGIC BELOW
# ------------------------
# Example: simple fetch prices (replace with your trading logic)
try:
    btc_price = client.get_price("BTC-USD")
    print("📈 Current BTC price:", btc_price)
except Exception as e:
    print(f"⚠️ get_price() error: {e}")

# Keep the bot running or integrate your strategy here
# For example, with Flask:
# from flask import Flask
# app = Flask(__name__)
# @app.route("/")
# def home():
#     return "Nija Trading Bot is live!"
# app.run(host="0.0.0.0", port=PORT)
