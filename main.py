#!/usr/bin/env python3
"""
NIJA Trading Bot - Render-ready
Ensures virtualenv packages load first and handles Coinbase API.
"""

import os
import sys

# -------------------------------------------------
# Ensure virtualenv packages are first in sys.path
# -------------------------------------------------
VENV_PATH = os.path.join(os.getcwd(), ".venv", "lib", "python3.13", "site-packages")
if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)

# -------------------------------------------------
# Load environment variables
# -------------------------------------------------
from dotenv import load_dotenv
load_dotenv()

# -------------------------------------------------
# Debug info to confirm virtualenv is used
# -------------------------------------------------
print(f"Python executable: {sys.executable}")
print(f"sys.path:\n  " + "\n  ".join(sys.path))

# -------------------------------------------------
# Try to import coinbase_advanced_py
# -------------------------------------------------
USE_LIVE = True
try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py import OK")
except ImportError as e:
    print("❌ coinbase_advanced_py import failed:", e)
    USE_LIVE = False

# -------------------------------------------------
# Fallback MockClient
# -------------------------------------------------
if not USE_LIVE:
    class MockClient:
        def get_account_balances(self):
            return {"USD": 10000.0, "BTC": 0.05}
        def place_order(self, *args, **kwargs):
            raise RuntimeError("DRY RUN: MockClient refuses to place orders")
    client = MockClient()
    LIVE_TRADING = False
    print("⚠️ Using MockClient (no live trading)")
else:
    # Initialize real client
    PEM_B64 = os.getenv("API_PEM_B64")
    PEM_PATH = "/tmp/my_coinbase_key.pem"
    if PEM_B64:
        with open(PEM_PATH, "w") as f:
            f.write(PEM_B64)
        print(f"✅ PEM written to {PEM_PATH}")
    client = cb.CoinbaseAdvancedAPIClient(
        pem_path=PEM_PATH,
        api_key=os.getenv("API_KEY"),
        api_secret=os.getenv("API_SECRET"),
        passphrase=os.getenv("API_PASSPHRASE")
    )
    LIVE_TRADING = True
    print("🚀 Live Coinbase client initialized")

# -------------------------------------------------
# Minimal Flask app for Render health check
# -------------------------------------------------
from flask import Flask, jsonify
app = Flask("nija_bot")

@app.route("/")
def home():
    return jsonify({
        "status": "NIJA Bot is running!",
        "LIVE_TRADING": LIVE_TRADING,
        "balances": client.get_account_balances() if hasattr(client, "get_account_balances") else {}
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    print(f"🚀 Starting NIJA Bot Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
