#!/usr/bin/env python3
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# -------------------
# Load environment
# -------------------
load_dotenv()
USE_MOCK = os.getenv("USE_MOCK", "False").lower() == "true"
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PASSPHRASE = os.getenv("API_PASSPHRASE")

app = Flask(__name__)

# -------------------
# Load Coinbase client
# -------------------
try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py imported successfully.")
except ImportError as e:
    print("❌ Failed to import coinbase_advanced_py:", e)
    raise e

client = None
if not USE_MOCK:
    try:
        client = cb.Coinbase(
            api_key=API_KEY,
            api_secret=API_SECRET,
            passphrase=API_PASSPHRASE
        )
        print("✅ Live Coinbase client initialized.")
    except Exception as e:
        print("❌ Failed to initialize Coinbase client:", e)
        raise e
else:
    print("⚡ MOCK mode active, no live client.")

# -------------------
# Example route
# -------------------
@app.route("/balances", methods=["GET"])
def balances():
    if USE_MOCK:
        return jsonify({"mock": True, "balances": {"BTC": 1.0, "USD": 1000}})
    try:
        accounts = client.get_accounts()
        return jsonify({"mock": False, "balances": accounts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------
# Webhook / trading endpoint example
# -------------------
@app.route("/trade", methods=["POST"])
def trade():
    if USE_MOCK:
        return jsonify({"mock": True, "status": "trade simulated"})
    try:
        data = request.get_json()
        # Example: implement your real trading logic here
        print("📈 Received trade request:", data)
        return jsonify({"mock": False, "status": "trade executed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------
# Main entry
# -------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
