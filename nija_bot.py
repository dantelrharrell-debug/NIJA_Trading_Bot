import os
import coinbase_advanced_py as cb

# Debug: Check environment variables
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")

if not api_key or not api_secret:
    print("❌ API_KEY or API_SECRET not set!")
else:
    print("✅ API_KEY and API_SECRET detected")

# Debug: Test importing the package and creating a client
try:
    client = cb.Client(api_key, api_secret)
    print("✅ coinbase_advanced_py imported and client created successfully!")
except Exception as e:
    print("❌ Error creating Coinbase client:", e)

# nija_bot.py
# Nija Trading Bot - Web Service Version

import os
import threading
import time
from flask import Flask
import coinbase_advanced_py as cb

# -----------------------
# Flask setup
# -----------------------
app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))  # Render injects PORT automatically

@app.route("/")
def heartbeat():
    return "Nija Trading Bot is alive! 🟢"

# -----------------------
# Trading Bot Loop
# -----------------------
def bot_loop():
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    live_trading = os.getenv("LIVE_TRADING", "False") == "True"

    if not api_key or not api_secret:
        print("❌ API_KEY or API_SECRET not set. Add them to environment variables.")
        return

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
