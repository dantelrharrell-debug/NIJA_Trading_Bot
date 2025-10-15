#!/usr/bin/env python3
import os
from pathlib import Path
from flask import Flask

# -----------------------
# Load Coinbase credentials
# -----------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")  # Path to PEM file

# Validate keys
if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set")

pem_path = Path(API_SECRET)
if not pem_path.is_file():
    print(f"⚠️ PEM file not found at {pem_path}, falling back to MockClient")
    USE_MOCK = True
else:
    USE_MOCK = False

# -----------------------
# Import Coinbase SDK
# -----------------------
if not USE_MOCK:
    import coinbase as cb
    try:
        client = cb.Client(API_KEY, str(pem_path))
        LIVE_TRADING = True
    except Exception as e:
        print(f"❌ Failed to initialize Coinbase client: {e}")
        USE_MOCK = True

# -----------------------
# Mock client fallback
# -----------------------
if USE_MOCK:
    class MockClient:
        def get_account_balances(self):
            return {"USD": 10000.0, "BTC": 0.05}

        def place_order(self, *args, **kwargs):
            print("⚠️ Mock order placed:", args, kwargs)

    client = MockClient()
    LIVE_TRADING = False

# -----------------------
# Print starting balances
# -----------------------
balances = client.get_account_balances()
print("💰 Starting balances:", balances)
print("🔒 LIVE_TRADING =", LIVE_TRADING)

# -----------------------
# Start Flask server
# -----------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "🚀 Nija Trading Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting NIJA Bot Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
