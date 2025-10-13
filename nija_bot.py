# safe_coinbase_bootstrap.py  -- paste at top of your bot (or replace your current import block)
import importlib, pkgutil, inspect, os, sys, traceback

def find_client_class():
    # candidates to try importing as a top-level module
    candidates = ["coinbase_advanced_py", "coinbase_advanced", "coinbase"]
    found = []

    for cand in candidates:
        try:
            mod = importlib.import_module(cand)
        except Exception:
            continue

        # 1) direct attribute
        if hasattr(mod, "Client"):
            return mod, getattr(mod, "Client"), f"{cand}.Client"

        # 2) search submodules for class named 'Client' (shallow)
        if hasattr(mod, "__path__"):
            for finder, name, ispkg in pkgutil.iter_modules(mod.__path__):
                fullname = f"{cand}.{name}"
                try:
                    sub = importlib.import_module(fullname)
                except Exception:
                    continue
                if hasattr(sub, "Client"):
                    return sub, getattr(sub, "Client"), f"{fullname}.Client"
                # inspect attributes for class named Client
                for nm in dir(sub):
                    try:
                        obj = getattr(sub, nm)
                    except Exception:
                        continue
                    if inspect.isclass(obj) and nm.lower() == "client":
                        return sub, obj, f"{fullname}.{nm}"

    # final sweep: any installed top-level module with 'coin' in name (slower)
    for info in pkgutil.iter_modules():
        if "coin" in (info.name or "").lower():
            try:
                mod = importlib.import_module(info.name)
            except Exception:
                continue
            for nm in dir(mod):
                try:
                    obj = getattr(mod, nm)
                except Exception:
                    continue
                if inspect.isclass(obj) and nm.lower() == "client":
                    return mod, obj, f"{info.name}.{nm}"

    return None, None, None

# Boot
print("🔍 Attempting to locate Coinbase Client class...")
mod, ClientClass, location = find_client_class()

if ClientClass is None:
    print("❌ Could not find a Client class in installed coinbase packages.")
    print("Installed packages on sys.path (first 40):")
    for p in sys.path[:40]:
        print("  ", p)
    # optional: list installed coin* top-level modules for debugging
    print("\nTop-level modules containing 'coin' (first 200):")
    for info in list(pkgutil.iter_modules())[:200]:
        if "coin" in (info.name or "").lower():
            print("  ", info.name)
    # Do NOT start trading — exit safely or set a flag the rest of the app can check.
    COINBASE_CLIENT = None
    COINBASE_CLIENT_LOCATION = None
else:
    print(f"✅ Found Client at: {location}")
    # create client from environment variables
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    API_SECRET = os.getenv("API_SECRET")
    if not API_KEY or not API_SECRET:
        print("❌ Missing API_KEY or API_SECRET in environment/.env — client will not be created.")
        COINBASE_CLIENT = None
        COINBASE_CLIENT_LOCATION = location
    else:
        try:
            # instantiate client; adapt if constructor signature differs
            client = ClientClass(API_KEY, API_SECRET)
            print("✅ Coinbase client created successfully (type: {})".format(type(client)))
            COINBASE_CLIENT = client
            COINBASE_CLIENT_LOCATION = location
        except Exception as e:
            print("❌ Error instantiating Client:", e)
            traceback.print_exc()
            COINBASE_CLIENT = None
            COINBASE_CLIENT_LOCATION = location

# Export names expected later in your bot
globals().update({
    "cb_client": COINBASE_CLIENT,
    "cb_client_location": COINBASE_CLIENT_LOCATION,
})
# === Coinbase Advanced Import (resilient) ===
print("🔍 Checking for coinbase_advanced_py module...")

cb = None
try:
    import coinbase_advanced_py as cb
    print("✅ Imported coinbase_advanced_py successfully!")
except ModuleNotFoundError:
    try:
        import coinbase_advanced as cb
        print("✅ Imported coinbase_advanced (fallback) successfully!")
    except ModuleNotFoundError:
        try:
            import coinbase as cb
            print("✅ Imported coinbase (legacy) successfully!")
        except ModuleNotFoundError:
            print("❌ Could not import any Coinbase module. Check installation.")
            import sys
            sys.exit(1)

# Once imported, you can safely use cb.Client
try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py imported successfully!")
except Exception as e:
    print("❌ Failed to import coinbase_advanced_py:", e)
    raise
print("🚀 Nija Trading Bot starting...")
import sys
print("Python executable:", sys.executable)
print("sys.path:", sys.path)
import os
import threading
import time
from flask import Flask
import coinbase_advanced_py as cb

# -----------------------
# Debug: Verify package & API keys
# -----------------------
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")

if not api_key or not api_secret:
    print("❌ API_KEY or API_SECRET not set!")
else:
    print("✅ API_KEY and API_SECRET detected")

try:
    client_test = cb.Client(api_key, api_secret)
    print("✅ coinbase_advanced_py imported and client created successfully!")
except Exception as e:
    print("❌ Error creating Coinbase client:", e)

# -----------------------
# Flask setup
# -----------------------
app = Flask(__name__)
PORT = int(os.environ.get("PORT", 10000))

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
            balances = client.get_account_balances()
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
