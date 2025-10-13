import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "coinbase-advanced-py==1.8.2"])
# nija_bot_web.py
import os
import time
import threading
from flask import Flask, jsonify
import coinbase_advanced_py as cb
from dotenv import load_dotenv

# ------------------------
# LOAD ENVIRONMENT VARIABLES
# ------------------------
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
LIVE_TRADING = os.getenv("LIVE_TRADING", "False").lower() == "true"
PORT = int(os.getenv("PORT", 10000))  # Render assigns $PORT automatically if not set

# ------------------------
# VALIDATION
# ------------------------
if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set. Add them to environment variables.")

# ------------------------
# INITIALIZE CLIENT
# ------------------------
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("✅ Coinbase client initialized using API_KEY + API_SECRET")
except Exception as e:
    raise SystemExit(f"❌ Failed to initialize Coinbase client: {e}")

# ------------------------
# BOT THREAD
# ------------------------
stop_flag = False
bot_thread = None

def bot_loop():
    global stop_flag
    while not stop_flag:
        try:
            btc_price = client.get_price("BTC-USD")
            print(f"📈 BTC-USD price: {btc_price}")
        except Exception as e:
            print(f"⚠️ Error fetching BTC price: {e}")
        time.sleep(10)  # adjust frequency of price checks / trading logic

def start_bot():
    global bot_thread
    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    bot_thread.start()
    print("🟢 Bot thread started")

def stop_bot():
    global stop_flag
    stop_flag = True
    if bot_thread:
        bot_thread.join()
    print("🛑 Bot stopped")

# ------------------------
# FLASK APP (Web Service)
# ------------------------
app = Flask(__name__)

@app.route("/status")
def status():
    try:
        btc_price = client.get_price("BTC-USD")
        return jsonify({
            "status": "running",
            "live_trading": LIVE_TRADING,
            "btc_usd": btc_price
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# ------------------------
# MAIN
# ------------------------
if __name__ == "__main__":
    print(f"LIVE_TRADING: {LIVE_TRADING}")
    print("✅ Environment variables loaded")
    start_bot()
    app.run(host="0.0.0.0", port=PORT)
