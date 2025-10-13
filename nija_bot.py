# -----------------------
# nija_bot.py
# -----------------------
import os
import time
import threading
import traceback
from flask import Flask, jsonify

# -----------------------
# Safe Coinbase bootstrap
# -----------------------
import importlib
import inspect
import pkgutil
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

def find_coinbase_client_class():
    candidates = ["coinbase_advanced_py", "coinbase_advanced", "coinbase"]
    for pkg_name in candidates:
        try:
            pkg = importlib.import_module(pkg_name)
        except ModuleNotFoundError:
            continue

        # top-level classes
        for name, obj in inspect.getmembers(pkg):
            if inspect.isclass(obj) and "client" in name.lower():
                return pkg, obj

        # submodules
        if hasattr(pkg, "__path__"):
            for finder, sub_name, ispkg in pkgutil.iter_modules(pkg.__path__):
                fullname = f"{pkg_name}.{sub_name}"
                try:
                    submod = importlib.import_module(fullname)
                except Exception:
                    continue
                for name, obj in inspect.getmembers(submod):
                    if inspect.isclass(obj) and "client" in name.lower():
                        return submod, obj
    return None, None

pkg, ClientClass = find_coinbase_client_class()
if ClientClass is None:
    print("❌ No usable Coinbase Client class found. Trading disabled.")
    cb_client = None
else:
    print(f"✅ Found Coinbase Client: {ClientClass}")
    if not API_KEY or not API_SECRET:
        print("❌ API_KEY or API_SECRET missing. Cannot instantiate client.")
        cb_client = None
    else:
        try:
            cb_client = ClientClass(API_KEY, API_SECRET)
            print(f"✅ Coinbase client created successfully! ({type(cb_client)})")
        except Exception as e:
            print("❌ Error creating Coinbase client:", e)
            traceback.print_exc()
            cb_client = None

# -----------------------
# Flask setup
# -----------------------
app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))

@app.route("/")
def heartbeat():
    return "Nija Trading Bot is alive! 🟢"

@app.route("/balances")
def balances():
    if cb_client is None:
        return jsonify({"error": "Coinbase client not available"}), 400
    try:
        accounts = cb_client.get_accounts()
        balances_data = [
            {"currency": acct.get("currency"), "balance": acct.get("balance", {}).get("amount")}
            for acct in accounts
        ]
        return jsonify({"balances": balances_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------
# Trading Bot Loop (RESTClient-compatible)
# -----------------------
def bot_loop():
    live_trading = os.getenv("LIVE_TRADING", "False") == "True"

    if cb_client is None:
        print("❌ Coinbase client not available. Bot cannot start.")
        return

    print(f"🟢 Bot thread started - LIVE_TRADING: {live_trading}")

    while True:
        try:
            accounts = cb_client.get_accounts()
            print("📊 Account Balances:")
            for acct in accounts:
                currency = acct.get("currency")
                balance = acct.get("balance", {}).get("amount")
                print(f" - {currency}: {balance}")

            # TODO: Add trading logic here
            if live_trading:
                print("⚡ Live trading logic would execute here...")

            time.sleep(10)
        except Exception as e:
            print("❌ Error in bot loop:", e)
            traceback.print_exc()
            time.sleep(5)

# -----------------------
# Start bot in background thread
# -----------------------
bot_thread = threading.Thread(target=bot_loop)
bot_thread.daemon = True
bot_thread.start()

# -----------------------
# Start Flask web server
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
