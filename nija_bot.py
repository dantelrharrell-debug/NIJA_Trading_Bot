#!/usr/bin/env python3
"""
Debug block to diagnose coinbase-advanced-py import issues on Render
"""

import sys
import os
import subprocess

print("🛠 Python executable:", sys.executable)
print("🛠 sys.path:")
for p in sys.path:
    print("   ", p)

# Show which packages are installed in the active environment
try:
    import pkg_resources
    installed = sorted([f"{p.key}=={p.version}" for p in pkg_resources.working_set])
    print("🛠 Installed packages in this environment:")
    for pkg in installed:
        print("   ", pkg)
except Exception as e:
    print("⚠️ Failed to list installed packages:", e)

# Show if the coinbase_advanced_py package exists on disk
venv_site = "/opt/render/project/src/.venv/lib/python3.13/site-packages"
package_path = os.path.join(venv_site, "coinbase_advanced_py")
print(f"🛠 Checking if coinbase_advanced_py exists at {package_path}: ", os.path.exists(package_path))

# Optional: test direct import in a subprocess for isolation
try:
    subprocess.check_call([sys.executable, "-c", "import coinbase_advanced_py"], shell=False)
    print("✅ Subprocess import test succeeded")
except subprocess.CalledProcessError:
    print("❌ Subprocess import test failed")

#!/usr/bin/env python3
"""
nija_bot.py
NIJA Bot: Robust Coinbase autodetector + safe fallback
"""

import os
import sys
import traceback
from flask import Flask, jsonify

# ---------------------------
# Ensure Render virtualenv packages are on sys.path
# ---------------------------
VENV_SITE_PACKAGES = "/opt/render/project/src/.venv/lib/python3.13/site-packages"
if VENV_SITE_PACKAGES not in sys.path:
    sys.path.insert(0, VENV_SITE_PACKAGES)

# ---------------------------
# Load .env
# ---------------------------
from dotenv import load_dotenv
load_dotenv()

# ---------------------------
# Attempt to import coinbase_advanced_py
# ---------------------------
USE_LIVE = True
try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py imported successfully")
except Exception as e:
    print("❌ coinbase_advanced_py import failed:", e)
    USE_LIVE = False

# ---------------------------
# Prepare PEM for Coinbase
# ---------------------------
PEM_B64 = os.getenv("API_PEM_B64", "")
PEM_PATH = "/tmp/my_coinbase_key.pem"
if PEM_B64:
    with open(PEM_PATH, "w") as f:
        f.write(PEM_B64)
    print(f"✅ PEM written to {PEM_PATH}")
else:
    print("⚠️ API_PEM_B64 not found")

# ---------------------------
# Initialize client or fallback to Mock
# ---------------------------
LIVE_TRADING = False
client = None

if USE_LIVE and PEM_B64:
    try:
        client = cb.CoinbaseAdvancedAPIClient(
            pem_path=PEM_PATH,
            api_key=os.getenv("API_KEY"),
            api_secret=os.getenv("API_SECRET"),
            passphrase=os.getenv("API_PASSPHRASE")
        )
        LIVE_TRADING = True
        print("🚀 Live Coinbase client initialized")
    except Exception as e:
        print("⚠️ Failed to initialize live Coinbase client:", e)
        USE_LIVE = False

if not USE_LIVE:
    class MockClient:
        def get_account_balances(self):
            return {"USD": 10000.0, "BTC": 0.05}
        def place_order(self, *a, **k):
            raise RuntimeError("DRY RUN: MockClient refuses orders")
    client = MockClient()
    print("⚠️ Using MockClient (no live trading)")

# ---------------------------
# Read balances
# ---------------------------
try:
    balances = client.get_account_balances()
    print(f"💰 Starting balances: {balances}")
except Exception as e:
    balances = {"error": str(e)}
    print("❌ Error reading balances:", type(e).__name__, e)

print(f"🔒 LIVE_TRADING = {LIVE_TRADING}")

# ---------------------------
# Minimal Flask server
# ---------------------------
app = Flask("nija_bot")

@app.route("/")
def home():
    return jsonify({
        "status": "NIJA Bot is running!",
        "LIVE_TRADING": LIVE_TRADING,
        "balances": balances
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    print(f"🚀 Starting NIJA Bot Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
