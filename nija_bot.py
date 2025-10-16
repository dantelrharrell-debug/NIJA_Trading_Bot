#!/usr/bin/env python3
import os
import traceback
from flask import Flask, request, jsonify

app = Flask(__name__)

# -------------------
# Determine mock mode
# -------------------
USE_MOCK = os.getenv("USE_MOCK", "False").lower() == "true"
cb = None  # Coinbase client placeholder

if not USE_MOCK:
    try:
        import coinbase_advanced_py as cb
        print("✅ coinbase_advanced_py imported successfully.")
    except ModuleNotFoundError:
        print("❌ Coinbase module NOT found. Switching to MOCK mode.")
        USE_MOCK = True
    except Exception as e:
        print("❌ Unexpected error importing Coinbase:", e)
        USE_MOCK = True

if USE_MOCK:
    print("⚠️ Running in MOCK mode. No live trades will be executed.")

# -------------------
# Environment variables
# -------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM_B64 = os.getenv("API_PEM_B64")
TV_WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET")

# -------------------
# Flask webhook route
# -------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")
    if secret != TV_WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 401

    # For demo: log payload
    print("Webhook received:", data)

    # Placeholder: execute trade only if not in mock mode
    if USE_MOCK:
        print("MOCK TRADE: Skipping real Coinbase execution.")
    else:
        try:
            # Example: cb.place_order(...)
            print("LIVE TRADE: executing order with Coinbase...")
        except Exception as e:
            print("❌ Error executing trade:", e)

    return jsonify({"status": "ok"}), 200

# -------------------
# Main entry point
# -------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
