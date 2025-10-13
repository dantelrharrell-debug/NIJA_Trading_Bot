# -----------------------
# nija_bot_safe.py
# -----------------------
import importlib
import inspect
import os
import pkgutil
import threading
import time
import traceback
from dotenv import load_dotenv
from flask import Flask

# -----------------------
# Load environment
# -----------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# -----------------------
# Safe Coinbase client bootstrap
# -----------------------
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
                return pkg_name, obj

        # inspect submodules
        if hasattr(pkg, "__path__"):
            for finder, sub_name, ispkg in pkgutil.iter_modules(pkg.__path__):
                fullname = f"{pkg_name}.{sub_name}"
                try:
                    submod = importlib.import_module(fullname)
                except Exception:
                    continue
                for name, obj in inspect.getmembers(submod):
                    if inspect.isclass(obj) and "client" in name.lower():
                        return fullname, obj
    return None, None

pkg_location, ClientClass = find_coinbase_client_class()

if ClientClass is None:
    print("❌ No usable Coinbase Client class found. Trading disabled.")
    COINBASE_CLIENT = None
else:
    print(f"✅ Found Coinbase Client: {ClientClass} at {pkg_location}")
    if not API_KEY or not API_SECRET:
        print("❌ API_KEY or API_SECRET missing. Cannot instantiate client.")
        COINBASE_CLIENT = None
    else:
        try:
            COINBASE_CLIENT = ClientClass(API_KEY, API_SECRET)
            print(f"✅ Coinbase client created successfully! ({type(COINBASE_CLIENT)})")
        except Exception as e:
            print("❌ Error creating Coinbase client:", e)
            traceback.print_exc()
            COINBASE_CLIENT = None

# safe export
cb_client = COINBASE_CLIENT

# -----------------------
# Flask setup
# -----------------------
app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))

@app.route("/")
def heartbeat():
    return "Nija Trading Bot is alive! 🟢"

# -----------------------
# Trading bot loop
# -----------------------
def bot_loop():
    live_trading = os.getenv("LIVE_TRADING", "False") == "True"

    if cb_client is None:
        print("❌ Coinbase client unavailable. Trading loop disabled.")
        return

    print(f"🟢 Bot thread started - LIVE_TRADING: {live_trading}")

    while True:
        try:
            balances = cb_client.get_account_balances()
            print("Balances:", balances)
            # TODO: Add trading logic here
            time.sleep(10)
        except Exception as e:
            print("❌ Error in bot loop:", e)
            time.sleep(5)

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
