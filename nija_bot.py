#!/usr/bin/env python3
# nija_bot.py - Nija Trading Bot (Web Service version)
# Includes runtime self-heal: installs coinbase-advanced-py if missing.

import importlib, sys, subprocess, os, threading, time
from flask import Flask

# -----------------------
# Runtime self-heal installer (safe)
# -----------------------
def ensure(pkg_import_name, pip_name):
    """
    Ensure importable module pkg_import_name exists. If not, pip install pip_name
    using the same Python executable running this script.
    Returns the imported module.
    """
    try:
        return importlib.import_module(pkg_import_name)
    except ModuleNotFoundError:
        print(f"⚠️ {pkg_import_name} not found — attempting runtime install: {pip_name}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", pip_name])
            print("✅ pip install succeeded.")
            return importlib.import_module(pkg_import_name)
        except Exception as e:
            print("❌ Runtime pip install failed:", e)
            raise

# Ensure Coinbase library is available (will install if missing)
cb = ensure("coinbase_advanced_py", "coinbase-advanced-py==1.8.2")

# -----------------------
# Debug info
# -----------------------
print("✅ Runtime env check")
print("Python executable:", sys.executable)
print("sys.path (head):", sys.path[:6])

# -----------------------
# Environment & Flask setup
# -----------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
LIVE_TRADING = os.getenv("LIVE_TRADING", "False").lower() == "true"
PORT = int(os.getenv("PORT", 10000))  # Render provides PORT for web services

app = Flask(__name__)

@app.route("/")
def heartbeat():
    return "Nija Trading Bot is alive! 🟢"

# -----------------------
# Bot logic (runs in background thread)
# -----------------------
def bot_loop():
    if not API_KEY or not API_SECRET:
        print("❌ API_KEY or API_SECRET not set. Add them to environment variables in Render.")
        return

    try:
        client = cb.Client(API_KEY, API_SECRET)
        print("✅ Coinbase client created")
    except Exception as e:
        print("❌ Failed to create Coinbase client:", e)
        return

    print(f"🟢 Bot thread started - LIVE_TRADING: {LIVE_TRADING}")

    while True:
        try:
            # Example safe call: fetch balances
            balances = client.get_account_balances()
            print("💰 Balances snapshot:", balances)

            # Example DRY_RUN trading logic
            if LIVE_TRADING:
                print("⚡ LIVE_TRADING enabled - implement trading logic here")
                # TODO: add real trade calls, e.g. client.place_order(...)
            else:
                print("ℹ️ DRY_RUN mode - no trades placed")

            time.sleep(10)
        except Exception as e:
            print("❌ Error in bot loop:", type(e).__name__, str(e))
            time.sleep(5)

# Start bot in background thread
bot_thread = threading.Thread(target=bot_loop)
bot_thread.daemon = True
bot_thread.start()

# -----------------------
# Run Flask to bind the port (Render requires bound port)
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
