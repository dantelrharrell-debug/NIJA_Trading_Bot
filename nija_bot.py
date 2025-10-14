#!/usr/bin/env python3
# nija_bot.py - Nija Trading Bot for Render

import sys
import os
import threading
import time
from flask import Flask

# -----------------------
# Debug: Python & Environment
# -----------------------
print("✅ Virtual environment activated")
print("Python executable:", sys.executable)
print("sys.path:", sys.path)

# -----------------------
# Debug: Test coinbase_advanced_py import
# -----------------------
try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py imported successfully!")
except ModuleNotFoundError:
    print("❌ coinbase_advanced_py NOT found. Check venv and requirements.txt")
    sys.exit(1)

# -----------------------
# Debug: Test API keys
# -----------------------
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")

if api_key and api_secret:
    print("✅ API_KEY and API_SECRET detected")
else:
    print("❌ API_KEY or API_SECRET missing. Add them in Render environment variables")
    sys.exit(1)

# -----------------------
# Flask setup
# -----------------------
app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))  # Render injects PORT

@app.route("/")
def heartbeat():
    return "Nija Trading Bot is alive! 🟢"

# -----------------------
# Trading Bot Loop
# -----------------------
def bot_loop():
    live_trading = os.getenv("LIVE_TRADING", "False") == "True"

    client = cb.Client(api_key, api_secret)
    print(f"🟢 Bot thread started - LIVE_TRADING: {live_trading}")

    while True:
        try:
            # Example: fetch balances
            balances = client.get_account_balances()
            print("Balances:", balances)

            # TODO: Add your trading logic here
            # Example: check price, place orders, etc.

            time.sleep(10)  # run loop every 10 seconds
        except Exception as e:
            print("❌ Error in bot loop:", e)
            time.sleep(5)  # wait before retry

# -----------------------
# Start bot in background thread
# -----------------------
bot_thread = threading.Thread(target=bot_loop)
bot_thread.daemon = True
bot_thread.start()

# -----------------------
# Start Flask web service
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
