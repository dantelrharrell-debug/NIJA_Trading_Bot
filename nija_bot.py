#!/usr/bin/env python3
"""
NIJA Trading Bot - Render-friendly bootstrap
Ensures virtualenv packages load first and handles Coinbase API.
"""

import os
import sys

# -------------------------------------------------
# Ensure Render virtualenv packages are first in sys.path
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
# Debug info to confirm virtualenv is being used
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

#!/usr/bin/env python3
"""
nija_bot.py
Robust Coinbase autodetector + safe fallback for Render.
Ensures coinbase-advanced-py is loaded from virtualenv and handles PEM credentials.
"""

import os
import sys
import traceback
from flask import Flask, jsonify
from dotenv import load_dotenv

# ---------------------------
# Ensure Render virtualenv packages are on sys.path
# ---------------------------
VENV_SITE_PACKAGES = "/opt/render/project/src/.venv/lib/python3.13/site-packages"
if VENV_SITE_PACKAGES not in sys.path:
    sys.path.insert(0, VENV_SITE_PACKAGES)

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()

# ---------------------------
# Helper logging
# ---------------------------
def log(*a, **k):
    print(*a, **k, flush=True)

# ---------------------------
# Attempt to import coinbase_advanced_py
# ---------------------------
USE_LIVE = True
try:
    import coinbase_advanced_py as cb_adv
    log("✅ coinbase_advanced_py imported successfully")
except Exception as e:
    log("❌ coinbase_advanced_py import failed:", e)
    USE_LIVE = False

# ---------------------------
# Prepare PEM file for Coinbase authentication
# ---------------------------
PEM_B64 = os.getenv("API_PEM_B64", "")
PEM_PATH = "/tmp/my_coinbase_key.pem"

if PEM_B64:
    with open(PEM_PATH, "w") as f:
        f.write(PEM_B64)
    log(f"✅ PEM written to {PEM_PATH}")
else:
    log("⚠️ API_PEM_B64 not found in environment variables")

# ---------------------------
# Initialize Coinbase client or fallback
# ---------------------------
LIVE_TRADING = False
client = None

def init_coinbase_client():
    global client, LIVE_TRADING

    # Try coinbase_advanced_py first
    if USE_LIVE and PEM_B64:
        try:
            client = cb_adv.CoinbaseAdvancedAPIClient(
                pem_path=PEM_PATH,
                api_key=os.getenv("API_KEY"),
                api_secret=os.getenv("API_SECRET"),
                passphrase=os.getenv("API_PASSPHRASE")
            )
            LIVE_TRADING = True
            log("🚀 Live CoinbaseAdvancedAPIClient initialized")
            return
        except Exception as e:
            log("⚠️ Failed to init CoinbaseAdvancedAPIClient:", type(e).__name__, e)

    # Fallback to MockClient
    class MockClient:
        def get_account_balances(self):
            return {"USD": 10000.0, "BTC": 0.05}
        def place_order(self, *a, **k):
            raise RuntimeError("DRY RUN: MockClient refuses to place orders")

    client = MockClient()
    LIVE_TRADING = False
    log("⚠️ Using MockClient (no live trading)")

init_coinbase_client()

# ---------------------------
# Read balances
# ---------------------------
try:
    balances = client.get_account_balances()
    log(f"💰 Starting balances: {balances}")
except Exception as e:
    balances = {"error": str(e)}
    log("❌ Error reading balances:", type(e).__name__, e)

log(f"🔒 LIVE_TRADING = {LIVE_TRADING}")

# ---------------------------
# Minimal Flask app
# ---------------------------
app = Flask("nija_bot")

@app.route("/")
def home():
    return jsonify({
        "status": "NIJA Bot is running!",
        "LIVE_TRADING": LIVE_TRADING,
        "balances": balances
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    log(f"🚀 Starting NIJA Bot Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
