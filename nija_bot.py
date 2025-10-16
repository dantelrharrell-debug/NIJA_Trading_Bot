#!/usr/bin/env python3
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ------------------------
# Flask app
# ------------------------
app = Flask(__name__)

# ------------------------
# Root route (for testing)
# ------------------------
@app.route("/")
def home():
    return "NIJA Trading Bot is running 🔥"

# ------------------------
# Webhook route
# ------------------------
WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")
    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 401
    # TODO: Add your webhook processing logic here
    return jsonify({"status": "received"})

# ------------------------
# Coinbase client setup
# ------------------------
USE_MOCK = os.getenv("USE_MOCK", "False").lower() == "true"

if not USE_MOCK:
    try:
        import coinbase_advanced_py as cb
        print("✅ coinbase_advanced_py imported successfully.")

        API_KEY = os.getenv("API_KEY")
        API_SECRET = os.getenv("API_SECRET")
        API_PASSPHRASE = os.getenv("API_PASSPHRASE")
        API_PEM_B64 = os.getenv("API_PEM_B64")

        client = cb.CoinbaseAdvancedPyClient(
            api_key=API_KEY,
            api_secret=API_SECRET,
            passphrase=API_PASSPHRASE,
            pem_b64=API_PEM_B64
        )
        print("✅ Coinbase client initialized for LIVE trading.")

    except Exception as e:
        print("⚠️ coinbase_advanced_py import failed:", e)
        USE_MOCK = True

if USE_MOCK:
    class MockClient:
        def place_order(self, *args, **kwargs):
            print("⚠️ Mock order placed:", args, kwargs)
    client = MockClient()
    print("⚠️ MockClient initialized (NO LIVE TRADING)")

# ------------------------
# Run Flask server
# ------------------------
if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=PORT)
