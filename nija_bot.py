#!/usr/bin/env python3

# 1️⃣ Load environment variables and validate keys
import os
from pathlib import Path

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set")

pem_path = Path(API_SECRET)
if not pem_path.is_file():
    raise SystemExit(f"❌ PEM file not found at {pem_path}")

# 2️⃣ Now import other modules
import coinbase_advanced_py as cb
from flask import Flask

# 3️⃣ Initialize client safely
client = cb.Client(API_KEY, pem_path)

# 4️⃣ Continue with your bot code...

#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import traceback

import coinbase

# ----------------------
# Load API credentials
# ----------------------
API_KEY = os.getenv("API_KEY")  # Your Coinbase API key (string)
API_SECRET = os.getenv("API_SECRET")  # Path to your PEM file

# Check credentials
if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set")

# Ensure PEM file exists
pem_path = Path(API_SECRET)
if not pem_path.is_file():
    print(f"❌ PEM file not found at {pem_path}")
    print("⚠️ Falling back to MockClient")
    LIVE_TRADING = False
else:
    LIVE_TRADING = True

# ----------------------
# Initialize Coinbase client
# ----------------------
try:
    if LIVE_TRADING:
        from coinbase.rest import RESTClient
        client = RESTClient(API_KEY, str(pem_path))
        print("✅ RESTClient initialized. LIVE_TRADING =", LIVE_TRADING)
    else:
        # Fallback MockClient
        class MockClient:
            def get_account_balances(self):
                return {"USD": 10000.0, "BTC": 0.05}

        client = MockClient()
        print("⚠️ Using MockClient. LIVE_TRADING =", LIVE_TRADING)
except Exception as e:
    print("❌ Error initializing RESTClient:")
    traceback.print_exc()
    print("⚠️ Falling back to MockClient")
    LIVE_TRADING = False
    class MockClient:
        def get_account_balances(self):
            return {"USD": 10000.0, "BTC": 0.05}
    client = MockClient()

# ----------------------
# Check starting balances
# ----------------------
try:
    balances = client.get_account_balances()
except Exception as e:
    balances = {"error": str(e)}

print("💰 Starting balances:", balances)

# ----------------------
# Flask server start
# ----------------------
from flask import Flask
app = Flask("nija_bot")

@app.route("/")
def home():
    return "NIJA Trading Bot is live!"

if __name__ == "__main__":
    print("🚀 Starting NIJA Bot Flask server...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)), debug=False)
