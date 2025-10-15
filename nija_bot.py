#!/usr/bin/env python3
import os
import coinbase_advanced as cb  # <-- fix here
from flask import Flask, jsonify

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

LIVE_TRADING = False
client = None

# Try live client
if API_KEY and API_SECRET:
    try:
        client = cb.Client(API_KEY, API_SECRET)
        LIVE_TRADING = True
        print("🟢 Live Coinbase client initialized. LIVE_TRADING=True")
    except Exception as e:
        print("❌ Failed to initialize live Coinbase client:", e)

# Fallback to mock
if not LIVE_TRADING:
    print("🧪 Using MockClient instead")
    class MockClient:
        def get_account_balances(self):
            return {'USD': 10000.0, 'BTC': 0.05, 'ETH': 0.3}
    client = MockClient()

balances = client.get_account_balances()
print(f"💰 Starting balances: {balances}")

app = Flask("nija_bot")

@app.route("/")
def home():
    return jsonify({
        "status": "NIJA Bot is running!",
        "LIVE_TRADING": LIVE_TRADING,
        "balances": balances
    })

if __name__ == "__main__":
    print("🚀 Starting NIJA Bot Flask server...")
    app.run(host="0.0.0.0", port=10000)

#!/usr/bin/env python3
import os
import coinbase_advanced_py as cb
from flask import Flask, jsonify

# ----------------------
# Load environment vars
# ----------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

LIVE_TRADING = False
client = None

# ----------------------
# Attempt to initialize Coinbase client
# ----------------------
if API_KEY and API_SECRET:
    try:
        client = cb.Client(API_KEY, API_SECRET)
        LIVE_TRADING = True
        print("🟢 Live Coinbase client initialized. LIVE_TRADING=True")
    except Exception as e:
        print("❌ Failed to initialize live Coinbase client:", e)

# ----------------------
# Fallback to MockClient
# ----------------------
if not LIVE_TRADING:
    print("🧪 Using MockClient instead")
    class MockClient:
        def get_account_balances(self):
            return {'USD': 10000.0, 'BTC': 0.05, 'ETH': 0.3}
    client = MockClient()

# ----------------------
# Print balances at startup
# ----------------------
balances = client.get_account_balances()
print(f"💰 Starting balances: {balances}")

# ----------------------
# Flask setup
# ----------------------
app = Flask("nija_bot")

@app.route("/")
def home():
    return jsonify({
        "status": "NIJA Bot is running!",
        "LIVE_TRADING": LIVE_TRADING,
        "balances": balances
    })

# ----------------------
# Start Flask server
# ----------------------
if __name__ == "__main__":
    print("🚀 Starting NIJA Bot Flask server...")
    app.run(host="0.0.0.0", port=10000)
