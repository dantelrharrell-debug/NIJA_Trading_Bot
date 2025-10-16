import sys
import importlib

try:
    import coinbase_advanced_py
    print("✅ coinbase_advanced_py is installed at:", coinbase_advanced_py.__file__)
except ModuleNotFoundError:
    print("❌ Coinbase module NOT found")
    print("Python executable:", sys.executable)
    print("sys.path:", sys.path)

#!/usr/bin/env python3
# 🥷 Nija Bot - Fully Live Coinbase Version with Logging
# ✅ Ready for Render and live trading

import os
import traceback
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# -------- Load environment variables --------
load_dotenv()
WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

# -------- Setup logging --------
LOG_FILE = "nija_bot.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)

# -------- Coinbase Client Setup --------
try:
    import coinbase_advanced_py as cb
    COINBASE_OK = True
except ModuleNotFoundError:
    COINBASE_OK = False
    logging.error("Coinbase LIVE connection FAILED: No module named 'coinbase_advanced_py'")

if COINBASE_OK:
    try:
        API_KEY = os.getenv("COINBASE_API_KEY")
        API_SECRET = os.getenv("COINBASE_API_SECRET")
        COINBASE = cb.Client(api_key=API_KEY, api_secret=API_SECRET)
        logging.info("Coinbase client initialized successfully.")
    except Exception as e:
        COINBASE_OK = False
        logging.error(f"Failed to initialize Coinbase client: {e}")

# -------- Flask Setup --------
app = Flask(__name__)

@app.route("/")
def home():
    if COINBASE_OK:
        return "🥷 Nija Bot is LIVE and Coinbase client ready!"
    else:
        return "⚠️ Nija Bot is LIVE but Coinbase client FAILED!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json() or {}
    secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")

    if secret != WEBHOOK_SECRET:
        logging.warning("Unauthorized webhook attempt.")
        return jsonify({"error": "unauthorized"}), 401

    logging.info(f"Webhook received: {data}")

    if not COINBASE_OK:
        logging.error("Coinbase client not available. Cannot execute order.")
        return jsonify({"error": "Coinbase client not available"}), 500

    try:
        action = data.get("action")  # "buy" or "sell"
        symbol = data.get("symbol")  # e.g., "BTC-USD"
        size = float(data.get("size", 0.001))  # crypto amount

        if action not in ["buy", "sell"]:
            logging.warning(f"Invalid action received: {action}")
            return jsonify({"error": "invalid action"}), 400

        logging.info(f"Executing {action} order: {size} {symbol}")
        order = COINBASE.create_order(
            product_id=symbol,
            side=action,
            type="market",
            size=str(size)
        )
        logging.info(f"Order executed: {order}")
        return jsonify({"status": "success", "order": order})
    except Exception as e:
        logging.error(f"Error executing order: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

# -------- Run Flask --------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    logging.info(f"Nija Bot starting on port {port}...")
    app.run(host="0.0.0.0", port=port)
