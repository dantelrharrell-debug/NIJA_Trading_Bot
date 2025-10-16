#!/usr/bin/env python3
import os
import sys
import traceback
from flask import Flask, request, jsonify

# -------------------
# Load environment
# -------------------
from dotenv import load_dotenv
load_dotenv()

# -------------------
# Determine mock mode
# -------------------
USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"

# -------------------
# Initialize Coinbase client
# -------------------
if not USE_MOCK:
    try:
        import coinbase_advanced_py as cb
        API_KEY = os.getenv("API_KEY")
        API_SECRET = os.getenv("API_SECRET")
        API_PEM_B64 = os.getenv("API_PEM_B64")

        client = cb.CoinbaseAdvanced(
            api_key=API_KEY,
            api_secret=API_SECRET,
            pem_b64=API_PEM_B64,
            sandbox=False  # set True if testing
        )
        print("✅ Coinbase client initialized in LIVE mode")
    except Exception as e:
        print("❌ Failed to initialize Coinbase client:", e)
        USE_MOCK = True
else:
    print("ℹ️ Running in MOCK mode (no real trades)")

# -------------------
# Initialize Flask
# -------------------
app = Flask(__name__)

WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")
    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 401

    # Example payload processing
    try:
        event_type = data.get("type", "unknown")
        print(f"🔔 Received webhook event: {event_type}")
        # Add trading logic here...
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# -------------------
# Test route
# -------------------
@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "NIJA Bot is running", "mock": USE_MOCK})

# -------------------
# Run locally (if needed)
# -------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
