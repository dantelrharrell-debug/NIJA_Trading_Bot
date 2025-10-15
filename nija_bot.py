#!/usr/bin/env python3
import os
import sys
from flask import Flask

# -------------------------------
# Coinbase Advanced API setup
# -------------------------------
try:
    from coinbase_advanced_py import CoinbaseAdvancedClient
    COINBASE_AVAILABLE = True
except ModuleNotFoundError:
    print("❌ coinbase_advanced_py not installed, using mock client")
    COINBASE_AVAILABLE = False

PEM_PATH = "/tmp/my_coinbase_key.pem"
PEM_CONTENT = os.getenv("COINBASE_PEM")

client = None
LIVE_TRADING = False

if COINBASE_AVAILABLE and PEM_CONTENT:
    # Write PEM file
    with open(PEM_PATH, "w") as f:
        f.write(PEM_CONTENT)
    print(f"✅ PEM written to {PEM_PATH}")

    try:
        client = CoinbaseAdvancedClient(pem_file=PEM_PATH)
        LIVE_TRADING = True
        print("✅ Live Coinbase client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Coinbase client: {e}")
        client = None
else:
    if not PEM_CONTENT:
        print("⚠️ COINBASE_PEM environment variable not set")
    client = None

# -------------------------------
# Balances (live or mock)
# -------------------------------
if LIVE_TRADING and client:
    try:
        balances = client.get_account_balances()
    except Exception as e:
        print(f"⚠️ Failed to fetch live balances: {e}")
        balances = {"USD": 10000.0, "BTC": 0.05}
else:
    print("⚠️ Using mock balances")
    balances = {"USD": 10000.0, "BTC": 0.05}

print(f"💰 Starting balances: {balances}")
print(f"🔒 LIVE_TRADING = {LIVE_TRADING}")

# -------------------------------
# Flask App Setup
# -------------------------------
app = Flask(__name__)

@app.route("/")
def index():
    return "🚀 Nija Trading Bot is running!"

# -------------------------------
# Run bot logic here (after this block)
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting NIJA Bot Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
