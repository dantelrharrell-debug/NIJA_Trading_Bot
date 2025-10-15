# ---------- Coinbase import & client setup ----------
# (paste here the code I gave you earlier that sets up COINBASE_CLIENT)
# ---------- END Coinbase setup ----------


# ---------- Flask setup + TradingView webhook ----------
from flask import Flask, request, jsonify
app = Flask(__name__)

WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

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
    if os.getenv("LIVE_TRADING", "False") == "True" and hasattr(COINBASE_CLIENT, "place_order"):
        result = COINBASE_CLIENT.place_order(symbol=symbol, side=action, size=size)
    else:
        result = {"status": "mock", "action": action, "symbol": symbol, "size": size}

    return jsonify({"ok": True, "result": result})
# ---------- END Flask webhook ----------

# ---------- BEGIN: Coinbase import & client setup (paste exactly) ----------
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Try both common package names so deployments don't break
coinbase_pkg = None
try:
    import coinbase_advanced_py as cb  # preferred import name used in some installs
    coinbase_pkg = 'coinbase_advanced_py'
except Exception:
    try:
        import coinbase as cb  # many wheels provide 'coinbase' package
        coinbase_pkg = 'coinbase'
    except Exception:
        cb = None
        coinbase_pkg = None

logger.info(f"coinbase package detected: {coinbase_pkg}")

# Minimal MockClient for safety (no live trades) used if real creds not provided
class MockClient:
    def __init__(self):
        logger.warning("Using MockClient (no live trading).")

    def place_order(self, *args, **kwargs):
        logger.info("MockClient.place_order called", args, kwargs)
        return {"status": "mock", "detail": "order simulated"}

# Create real client only when env vars are present and package loaded
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")
COINBASE_API_PASSPHRASE = os.getenv("COINBASE_API_PASSPHRASE")
COINBASE_PRIVATE_KEY_PEM = os.getenv("COINBASE_PRIVATE_KEY_PEM_PATH")  # optional path

client = None
if cb is not None and COINBASE_API_KEY and (COINBASE_API_SECRET or COINBASE_PRIVATE_KEY_PEM):
    try:
        # Try a few common constructors depending on package variant.
        # 1) coinbase_advanced_py may expose a Client class in module root:
        if hasattr(cb, "Client"):
            client = cb.Client(api_key=COINBASE_API_KEY,
                               api_secret=COINBASE_API_SECRET,
                               passphrase=COINBASE_API_PASSPHRASE)
        # 2) Some installs expose rest API as cb.rest.Client
        elif hasattr(cb, "rest") and hasattr(cb.rest, "Client"):
            client = cb.rest.Client(api_key=COINBASE_API_KEY,
                                    api_secret=COINBASE_API_SECRET,
                                    passphrase=COINBASE_API_PASSPHRASE)
        # 3) Fallback: create a simple wrapper that raises if used (safety)
        else:
            logger.warning("Coinbase package imported but no known Client constructor found. Falling back to MockClient.")
            client = MockClient()

        logger.info("Real Coinbase client created. LIVE_TRADING only enabled if LIVE_TRADING env var == 'True'.")

    except Exception as e:
        logger.exception("Failed to initialize real Coinbase client, using MockClient. Exception: %s", e)
        client = MockClient()
else:
    logger.warning("Coinbase credentials not found or package missing; using MockClient.")
    client = MockClient()

# Expose client variable for the rest of your bot code to use
COINBASE_CLIENT = client
# ---------- END: Coinbase import & client setup ----------

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
