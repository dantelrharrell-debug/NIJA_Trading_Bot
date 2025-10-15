import os
import sys

LIVE_TRADING = False
client = None

# -------------------------------
# Coinbase PEM / Live trading setup
# -------------------------------
try:
    from coinbase_advanced_py import CoinbaseAdvancedClient
except ModuleNotFoundError:
    print("❌ coinbase_advanced_py not installed. Using MockClient.")
    CoinbaseAdvancedClient = None

PEM_PATH = "/tmp/my_coinbase_key.pem"
PEM_CONTENT = os.getenv("COINBASE_PEM")

if PEM_CONTENT:
    with open(PEM_PATH, "w") as f:
        f.write(PEM_CONTENT)
    print(f"✅ PEM written to {PEM_PATH}")

    if CoinbaseAdvancedClient:
        try:
            client = CoinbaseAdvancedClient(pem_file=PEM_PATH)
            LIVE_TRADING = True
            print("🟢 ✅ Live Coinbase client initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Coinbase client: {e}")
            client = None
else:
    print("⚠️ COINBASE_PEM not set, using mock balances")

# -------------------------------
# Balances
# -------------------------------
if LIVE_TRADING and client:
    try:
        balances = client.get_account_balances()
        print(f"💰 Starting balances: {balances}")
    except Exception as e:
        print(f"❌ Failed to fetch balances: {e}")
        LIVE_TRADING = False
        balances = {"USD": 10000.0, "BTC": 0.05}
else:
    balances = {"USD": 10000.0, "BTC": 0.05}
    if not LIVE_TRADING:
        print("⚠️ Using mock balances")
print(f"🔒 LIVE_TRADING = {LIVE_TRADING}")

# -------------------------------
# Start your Flask bot
# -------------------------------
from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "NIJA Bot is running 🔥"

if __name__ == "__main__":
    print("🚀 Starting NIJA Bot Flask server on port 10000...")
    app.run(host="0.0.0.0", port=10000)
