#!/usr/bin/env python3
"""
NIJA Trading Bot - Render-ready
Supports live Coinbase trades if credentials exist,
otherwise uses MockClient for dry run.
"""

import os
import sys
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# -------------------------------------------------
# Ensure virtualenv packages are first in sys.path
# -------------------------------------------------
VENV_PATH = os.path.join(os.getcwd(), ".venv", "lib", "python3.13", "site-packages")
if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)
    print(f"Added virtualenv site-packages to sys.path: {VENV_PATH}")

# -------------------------------------------------
# Load environment variables
# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# Logging
# -------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nija_bot")

# -------------------------------------------------
# Coinbase import & client setup
# -------------------------------------------------
cb = None
COINBASE_CLIENT = None
USE_LIVE = True

try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py import OK")
except ImportError:
    try:
        import coinbase_advanced as cb
        print("✅ coinbase_advanced import OK")
    except ImportError as e:
        print("❌ Failed to import Coinbase client:", e)
        USE_LIVE = False

# Fallback MockClient
class MockClient:
    def get_account_balances(self):
        return {"USD": 10000.0, "BTC": 0.05}

    def place_order(self, *args, **kwargs):
        logger.info("MockClient.place_order called", args, kwargs)
        return {"status": "mock", "detail": "order simulated"}

if not USE_LIVE:
    COINBASE_CLIENT = MockClient()
    LIVE_TRADING = False
    print("⚠️ Using MockClient (no live trading)")
else:
    try:
        # Write PEM file if base64 exists
        PEM_B64 = os.getenv("API_PEM_B64")
        PEM_PATH = "/tmp/coinbase_key.pem"
        if PEM_B64:
            with open(PEM_PATH, "w") as f:
                f.write(PEM_B64)
            print(f"✅ PEM written to {PEM_PATH}")

        # Initialize client
        COINBASE_CLIENT = cb.CoinbaseAdvancedAPIClient(
            pem_path=PEM_PATH if PEM_B64 else None,
            api_key=os.getenv("API_KEY"),
            api_secret=os.getenv("API_SECRET"),
            passphrase=os.getenv("API_PASSPHRASE"),
        )
        LIVE_TRADING = True
        print("🚀 Live Coinbase client initialized")
    except Exception as e:
        logger.exception("Failed to initialize real Coinbase client, using MockClient.")
        COINBASE_CLIENT = MockClient()
        LIVE_TRADING = False

# -------------------------------------------------
# Flask setup
# -------------------------------------------------
app = Flask("nija_bot")
WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

@app.route("/")
def home():
    return jsonify({
        "status": "NIJA Bot is running!",
        "LIVE_TRADING": LIVE_TRADING,
        "balances": COINBASE_CLIENT.get_account_balances() if hasattr(COINBASE_CLIENT, "get_account_balances") else {}
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")
    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 401

    # parse TradingView message
    action = data.get("action")
    symbol = data.get("symbol")
    size = data.get("size")

    # Trigger order (real if LIVE_TRADING=True, else mock)
    if LIVE_TRADING and hasattr(COINBASE_CLIENT, "place_order"):
        try:
            result = COINBASE_CLIENT.place_order(symbol=symbol, side=action, size=size)
        except Exception as e:
            logger.exception("Failed to place live order")
            result = {"status": "error", "detail": str(e)}
    else:
        result = {"status": "mock", "action": action, "symbol": symbol, "size": size}

    return jsonify({"ok": True, "result": result})

# -------------------------------------------------
# Run Flask server
# -------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    print(f"🚀 Starting NIJA Bot Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
