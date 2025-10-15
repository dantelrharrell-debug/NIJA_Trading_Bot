# nija_bot.py (top)
import importlib, sys

def get_coinbase_module():
    # try the obvious names in order
    candidates = ["coinbase_advanced_py", "coinbase_advanced", "coinbase"]
    for name in candidates:
        try:
            return importlib.import_module(name)
        except ModuleNotFoundError:
            continue
    raise ModuleNotFoundError("No coinbase-advanced package found; expected one of: " + ", ".join(candidates))

cb = get_coinbase_module()
print("Using coinbase package:", cb.__name__)
# Inspect available public names for you to adapt the rest of the code
print("Public members:", [n for n in dir(cb) if not n.startswith('_')])
# Optionally: print help or available submodules
# import pkgutil
# print([m.name for m in pkgutil.iter_modules(cb.__path__)] if hasattr(cb, "__path__") else "no subpackages")

#!/usr/bin/env python3
import os
import coinbase_advanced_py as cb  # ✅ correct import
from flask import Flask, jsonify

# ----------------------
# Load environment variables
# ----------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

LIVE_TRADING = False
client = None

# ----------------------
# Initialize Coinbase client
# ----------------------
if API_KEY and API_SECRET:
    try:
        client = cb.Client(API_KEY, API_SECRET)
        LIVE_TRADING = True
        print("🟢 Live Coinbase client initialized. LIVE_TRADING=True")
    except Exception as e:
        print("❌ Failed to initialize live Coinbase client:", e)

# ----------------------
# Fallback to MockClient if live fails
# ----------------------
if not LIVE_TRADING:
    print("🧪 Using MockClient instead")
    class MockClient:
        def get_account_balances(self):
            return {'USD': 10000.0, 'BTC': 0.05, 'ETH': 0.3}
    client = MockClient()

# ----------------------
# Print balances at startup
# ----------------------
balances = client.get_account_balances()
print(f"💰 Starting balances: {balances}")

# ----------------------
# Flask setup
# ----------------------
app = Flask("nija_bot")

@app.route("/")
def home():
    return jsonify({
        "status": "NIJA Bot is running!",
        "LIVE_TRADING": LIVE_TRADING,
        "balances": balances
    })

# ----------------------
# Start Flask server
# ----------------------
if __name__ == "__main__":
    print("🚀 Starting NIJA Bot Flask server...")
    app.run(host="0.0.0.0", port=10000)
