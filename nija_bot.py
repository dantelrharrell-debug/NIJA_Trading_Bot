# nija_bot.py
import os
import time
import traceback
import threading
from flask import Flask, jsonify, request, abort

# ------------------------
# ENVIRONMENT
# ------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
LIVE_TRADING = os.getenv("LIVE_TRADING", "False").lower() == "true"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")  # recommended for protecting control endpoints

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set. Add them to environment variables.")

print("✅ Environment variables loaded")
print(f"LIVE_TRADING: {LIVE_TRADING}")

# ------------------------
# FLASK APP
# ------------------------
app = Flask("nija-bot-web")

# Shared state
_bot_thread = None
_stop_event = threading.Event()
_client_lock = threading.Lock()
_coinbase_client = None
_last_status = {"running": False, "last_error": None, "last_price": None}

# ------------------------
# COINBASE CLIENT INIT (retry loop)
# ------------------------
def init_coinbase_client():
    global _coinbase_client
    while True:
        try:
            import coinbase_advanced_py as cb
            client = cb.Client(API_KEY, API_SECRET)
            with _client_lock:
                _coinbase_client = client
            print("✅ Coinbase client initialized")
            return client
        except ModuleNotFoundError:
            print("⚠️ coinbase_advanced_py not installed. Retrying in 10s...")
            _last_status["last_error"] = "coinbase_advanced_py not installed"
        except Exception as e:
            print(f"⚠️ Failed to initialize Coinbase client: {e}. Retrying in 10s...")
            _last_status["last_error"] = str(e)
        time.sleep(10)

# ------------------------
# BOT LOOP
# ------------------------
def bot_loop():
    global _coinbase_client, _last_status
    print("🟢 Bot thread started")
    _last_status["running"] = True
    try:
        client = init_coinbase_client()
        # initial account check
        try:
            accounts = client.get_account_balances()
            print("💰 Accounts snapshot:", accounts)
        except Exception as e:
            print("⚠️ get_account_balances() error:", e)
            _last_status["last_error"] = str(e)
        # main loop
        while not _stop_event.is_set():
            try:
                with _client_lock:
                    client = _coinbase_client
                if client is None:
                    # if client lost, re-init
                    client = init_coinbase_client()
                btc_price = client.get_price("BTC-USD")
                print("📈 Current BTC price:", btc_price)
                _last_status["last_price"] = btc_price
                _last_status["last_error"] = None
                # TODO: place trading logic here
            except Exception as e:
                print("⚠️ Error in bot loop:", e)
                _last_status["last_error"] = str(e)
            # adjust sleep to your needs
            time.sleep(10)
    except Exception:
        print("❌ Bot thread crashed")
        traceback.print_exc()
        _last_status["last_error"] = "bot crashed: " + traceback.format_exc()
    finally:
        _last_status["running"] = False
        print("🛑 Bot thread exiting")

# ------------------------
# CONTROL HELPERS
# ------------------------
def start_bot_thread():
    global _bot_thread, _stop_event
    if _bot_thread and _bot_thread.is_alive():
        return False
    _stop_event = threading.Event()
    _bot_thread = threading.Thread(target=bot_loop, daemon=True)
    _bot_thread.start()
    return True

def stop_bot_thread():
    global _bot_thread, _stop_event
    if not _bot_thread:
        return False
    _stop_event.set()
    _bot_thread.join(timeout=15)
    return True

def check_admin_auth():
    if ADMIN_TOKEN:
        token = request.headers.get("Authorization", "")
        if not token.startswith("Bearer "):
            abort(401)
        if token.split(" ", 1)[1] != ADMIN_TOKEN:
            abort(401)

# ------------------------
# FLASK ROUTES
# ------------------------
@app.route("/", methods=["GET"])
def root():
    return "Nija Trading Bot (web) — running ✅"

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "bot_running": _last_status["running"]})

@app.route("/status", methods=["GET"])
def status():
    return jsonify(_last_status)

@app.route("/start", methods=["POST"])
def start():
    check_admin_auth()
    started = start_bot_thread()
    return jsonify({"started": started, "running": _last_status["running"]})

@app.route("/stop", methods=["POST"])
def stop():
    check_admin_auth()
    stopped = stop_bot_thread()
    return jsonify({"stopped": stopped, "running": _last_status["running"]})

# ------------------------
# Ensure bot thread starts when module imported (gunicorn will import module per worker)
# We rely on using a single gunicorn worker (see startCommand).
# ------------------------
if os.getenv("AUTO_START", "True").lower() in ("1", "true", "yes"):
    try:
        start_bot_thread()
    except Exception as e:
        print("⚠️ Could not auto-start bot thread:", e)
