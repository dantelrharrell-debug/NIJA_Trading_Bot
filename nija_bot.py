# nija_bot.py  (web-service-friendly)
import os
import time
import traceback
import threading
from flask import Flask, jsonify, request, abort

# ENV
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
LIVE_TRADING = os.getenv("LIVE_TRADING", "False").lower() == "true"
PORT = int(os.getenv("PORT", "10000"))
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")  # optional: set a token to protect control endpoints

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set.")

print("✅ Environment variables loaded")
print(f"LIVE_TRADING: {LIVE_TRADING}, PORT: {PORT}")

# CLIENT INIT (retry loop)
def init_client():
    while True:
        try:
            import coinbase_advanced_py as cb
            client = cb.Client(API_KEY, API_SECRET)
            print("✅ Coinbase client initialized")
            return client
        except ModuleNotFoundError:
            print("⚠️ coinbase_advanced_py not installed. Retrying in 10s...")
        except Exception as e:
            print(f"⚠️ Failed to initialize client: {e}. Retrying in 10s...")
        time.sleep(10)

# BOT LOOP
stop_flag = threading.Event()

def bot_loop(client):
    print("✅ Bot loop started")
    while not stop_flag.is_set():
        try:
            btc_price = client.get_price("BTC-USD")
            print("📈 Current BTC price:", btc_price)
            # TODO: place your trading logic here
        except Exception as e:
            print(f"⚠️ Error in bot loop: {e}")
        time.sleep(10)

# Start client + bot thread
client = init_client()
try:
    accounts = client.get_account_balances()
    print("💰 Accounts snapshot:", accounts)
except Exception as e:
    print("⚠️ accounts fetch error:", e)

bot_thread = threading.Thread(target=bot_loop, args=(client,), daemon=True)
bot_thread.start()

# Minimal Flask web app for Render port binding and health/control endpoints
app = Flask("nija-bot")

@app.route("/", methods=["GET"])
def home():
    return "Nija Trading Bot (web) — running ✅"

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "live_trading": LIVE_TRADING})

# protected endpoint to gracefully stop/start (optional)
def check_admin_auth():
    if ADMIN_TOKEN:
        token = request.headers.get("Authorization", "")
        if token != f"Bearer {ADMIN_TOKEN}":
            abort(401)

@app.route("/stop", methods=["POST"])
def stop():
    check_admin_auth()
    stop_flag.set()
    return jsonify({"status": "stopping"})

@app.route("/start", methods=["POST"])
def start():
    check_admin_auth()
    if bot_thread.is_alive():
        return jsonify({"status": "already running"})
    # re-init client and restart thread (simple approach)
    global client, bot_thread, stop_flag
    stop_flag = threading.Event()
    client = init_client()
    bot_thread = threading.Thread(target=bot_loop, args=(client,), daemon=True)
    bot_thread.start()
    return jsonify({"status": "started"})

if __name__ == "__main__":
    # Listen on Render's PORT
    app.run(host="0.0.0.0", port=PORT)
