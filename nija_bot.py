# -----------------------
# nija_bot_autofix.py
# -----------------------
import importlib
import inspect
import os
import pkgutil
import subprocess
import sys
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
# Ensure correct Coinbase package
# -----------------------
def ensure_coinbase_client():
    """
    Ensures a usable coinbase client exists.
    Attempts to downgrade/install if Client class missing.
    """
    candidates = ["coinbase_advanced_py", "coinbase_advanced", "coinbase"]

    for pkg_name in candidates:
        try:
            pkg = importlib.import_module(pkg_name)
        except ModuleNotFoundError:
            continue

        # top-level class check
        for name, obj in inspect.getmembers(pkg):
            if inspect.isclass(obj) and "client" in name.lower():
                print(f"✅ Found Client in {pkg_name}")
                return obj

        # submodule check
        if hasattr(pkg, "__path__"):
            for finder, sub_name, ispkg in pkgutil.iter_modules(pkg.__path__):
                fullname = f"{pkg_name}.{sub_name}"
                try:
                    submod = importlib.import_module(fullname)
                except Exception:
                    continue
                for name, obj in inspect.getmembers(submod):
                    if inspect.isclass(obj) and "client" in name.lower():
                        print(f"✅ Found Client in {fullname}")
                        return obj

    # Fallback: suggest downgrade for coinbase_advanced_py
    try:
        import coinbase_advanced_py as cap
        print("🔍 Client class missing in coinbase_advanced_py. Attempting fallback to v1.7.4...")
        subprocess.run([sys.executable, "-m", "pip", "install", "coinbase-advanced-py==1.7.4"], check=True)
        import importlib
        importlib.reload(cap)
        for name, obj in inspect.getmembers(cap):
            if inspect.isclass(obj) and "client" in name.lower():
                print("✅ Found Client after downgrade!")
                return obj
    except Exception as e:
        print("❌ Could not fix coinbase_advanced_py automatically:", e)

    print("❌ No usable Coinbase Client found.")
    return None

# -----------------------
# Instantiate client
# -----------------------
ClientClass = ensure_coinbase_client()
if ClientClass is None:
    COINBASE_CLIENT = None
else:
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
