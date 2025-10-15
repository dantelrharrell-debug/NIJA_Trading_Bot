#!/usr/bin/env python3
"""
NIJA Trading Bot - Render-ready
Flask + Coinbase client + TradingView webhook
"""

import os
import sys
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# ---------------------------
# Load env vars
# ---------------------------
load_dotenv()
WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

# ---------------------------
# Logginghttps://dashboard.render.com/web/srv-d3nld22dbo4c73d3a7k0/deploys/dep-d3o020ngi27c73cue34g
# ---------------------------
logger = logging.getLogger(__name__)

# ---------------------------
# Ensure virtualenv packages load first (Render-specific)
# ---------------------------
VENV_PATH = os.path.join(os.getcwd(), ".venv", "lib", "python3.13", "site-packages")
if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)

print(f"Python executable: {sys.executable}")
print(f"sys.path:\n  " + "\n  ".join(sys.path))

# ---------------------------
# Coinbase client setup
# ---------------------------
USE_LIVE = True
try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py import OK")
except ImportError:
    print("❌ coinbase_advanced_py import failed")
    USE_LIVE = False

if not USE_LIVE or not os.getenv("API_KEY"):
    class MockClient:
        def get_account_balances(self):
            return {"USD": 10000.0, "BTC": 0.05}

        def place_order(self, *args, **kwargs):
            logger.info("MockClient.place_order called", args, kwargs)
            return {"status": "mock", "detail": "order simulated"}

    COINBASE_CLIENT = MockClient()
    LIVE_TRADING = False
    print("⚠️ Using MockClient (no live trading)")
else:
    PEM_B64 = os.getenv("API_PEM_B64")
    PEM_PATH = "/tmp/my_coinbase_key.pem"
    if PEM_B64:
        with open(PEM_PATH, "w") as f:
            f.write(PEM_B64)
        print(f"✅ PEM written to {PEM_PATH}")
    COINBASE_CLIENT = cb.CoinbaseAdvancedAPIClient(
        pem_path=PEM_PATH,
        api_key=os.getenv("API_KEY"),
        api_secret=os.getenv("API_SECRET"),
        passphrase=os.getenv("API_PASSPHRASE")
    )
    LIVE_TRADING = True
    print("🚀 Live Coinbase client initialized")

# ---------------------------
# Flask app + TradingView webhook
# ---------------------------
app = Flask("nija_bot")

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

    action = data.get("action")
    symbol = data.get("symbol")
    size = data.get("size")

    if LIVE_TRADING and hasattr(COINBASE_CLIENT, "place_order"):
        result = COINBASE_CLIENT.place_order(symbol=symbol, side=action, size=size)
    else:
        result = {"status": "mock", "action": action, "symbol": symbol, "size": size}

    return jsonify({"ok": True, "result": result})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    print(f"🚀 Starting NIJA Bot Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
