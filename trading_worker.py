#!/usr/bin/env python3
import os
import sys

# Activate virtual environment (Render default)
venv_path = os.path.join(os.path.dirname(__file__), ".venv", "bin", "activate_this.py")
if os.path.exists(venv_path):
    with open(venv_path) as f:
        exec(f.read(), dict(__file__=venv_path))

# Ensure pip-installed packages are on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".venv", "lib", "python3.11", "site-packages"))

#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM_B64 = os.getenv("API_PEM_B64")
PASSPHRASE = os.getenv("PASSPHRASE")  # optional, only if required
USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"
LIVE_TRADING = os.getenv("LIVE_TRADING", "0") == "1"
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

# -----------------------------
# Initialize Coinbase client
# -----------------------------
from coinbase_advanced_py import CoinbaseClient

SANDBOX = USE_MOCK or not LIVE_TRADING

client = CoinbaseClient(
    api_key=API_KEY,
    api_secret=API_SECRET,
    passphrase=PASSPHRASE,
    pem_b64=API_PEM_B64,
    sandbox=SANDBOX
)

print(f"✅ Coinbase client initialized. Sandbox={SANDBOX}, Mock={USE_MOCK}, Live={LIVE_TRADING}")

# -----------------------------
# Optional: Print account balances for verification
# -----------------------------
try:
    accounts = client.get_accounts()
    print("Your Coinbase balances:")
    for acc in accounts:
        print(f"{acc['currency']}: {acc['balance']}")
except Exception as e:
    print("⚠️ Could not fetch accounts:", e)

# -----------------------------
# Flask webhook for TradingView signals
# -----------------------------
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")

    if secret != TV_WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 401

    signal = data.get("signal")
    pair = data.get("pair", "BTC-USD")
    amount = data.get("amount", 0.001)  # default small trade

    print(f"🔔 Received signal: {signal} for {pair}, amount={amount}")

    if USE_MOCK or not LIVE_TRADING:
        print("🧪 Mock trade executed (no real funds).")
        order = {"mock": True, "signal": signal, "pair": pair, "amount": amount}
    else:
        try:
            if signal == "buy":
                order = client.buy(pair, amount)
            elif signal == "sell":
                order = client.sell(pair, amount)
            else:
                order = None
                print("⚠️ Unknown signal received.")
            print("✅ Order response:", order)
        except Exception as e:
            order = None
            print("❌ Trade failed:", e)

    return jsonify({"status": "ok", "order": order})

# -----------------------------
# Run Flask server (Render)
# -----------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
