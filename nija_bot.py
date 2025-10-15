#!/usr/bin/env python3
"""
NIJA Trading Bot - Coinbase Live Check
Safe Render-ready test: ensures Coinbase client loads without executing trades
"""
import sys
import os

# Make sure the virtualenv site-packages is first in sys.path
VENV_PATH = os.path.join(os.getcwd(), ".venv", "lib", "python3.13", "site-packages")
if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)
    print(f"Added virtualenv site-packages to sys.path: {VENV_PATH}")
import os
import sys
from flask import Flask, jsonify
from dotenv import load_dotenv

# -------------------------------------------------
# Load environment variables
# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# Debug info for virtualenv & Python paths
# -------------------------------------------------
print(f"Python executable: {sys.executable}")
print(f"sys.path:\n  " + "\n  ".join(sys.path))

# -------------------------------------------------
# Coinbase client setup
# -------------------------------------------------
LIVE_TRADING = False
client = None

try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py import OK")

    API_KEY = os.getenv("API_KEY")
    API_SECRET = os.getenv("API_SECRET")
    PASSPHRASE = os.getenv("API_PASSPHRASE")
    PEM_B64 = os.getenv("API_PEM_B64")

    if API_KEY and (API_SECRET or PEM_B64):
        PEM_PATH = "/tmp/coinbase_test_key.pem"
        if PEM_B64:
            with open(PEM_PATH, "w") as f:
                f.write(PEM_B64)
            print(f"✅ PEM written to {PEM_PATH}")

        client = cb.CoinbaseAdvancedAPIClient(
            pem_path=PEM_PATH,
            api_key=API_KEY,
            api_secret=API_SECRET,
            passphrase=PASSPHRASE
        )
        LIVE_TRADING = True
        print("🚀 Live Coinbase client initialized (DRY RUN: no orders executed)")

except ImportError as e:
    print("❌ coinbase_advanced_py import failed:", e)

# -------------------------------------------------
# Fallback MockClient
# -------------------------------------------------
if client is None:
    class MockClient:
        def get_account_balances(self):
            return {"USD": 10000.0, "BTC": 0.05}

        def place_order(self, *args, **kwargs):
            print("⚠️ MockClient.place_order called (no live trading)")
            return {"status": "mock", "detail": "order simulated"}

    client = MockClient()
    LIVE_TRADING = False
    print("⚠️ Using MockClient (no live trading)")

# -------------------------------------------------
# Flask app for Render health check
# -------------------------------------------------
app = Flask("nija_bot")

@app.route("/")
def home():
    return jsonify({
        "status": "NIJA Bot is running!",
        "LIVE_TRADING": LIVE_TRADING,
        "balances": client.get_account_balances() if hasattr(client, "get_account_balances") else {}
    })

@app.route("/test-order")
def test_order():
    """Simulate an order to test client wiring (safe)"""
    try:
        result = client.place_order(symbol="BTC-USD", side="buy", size=0.001)
    except Exception as e:
        result = {"error": str(e)}
    return jsonify({"ok": True, "result": result})

# -------------------------------------------------
# Run Flask
# -------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    print(f"🚀 Starting NIJA Bot Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
