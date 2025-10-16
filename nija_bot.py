#!/usr/bin/env python3
import os
import sys
import traceback
from flask import Flask, request, jsonify

# -------------------------------
# Environment & Trading Settings
# -------------------------------
USE_MOCK = os.getenv("USE_MOCK", "False").lower() == "true"  # False on Render
FORCE_LIVE = True        # Force live trading
FORCE_TRADING = True     # Force trades to execute

# -------------------------------
# Initialize Flask
# -------------------------------
app = Flask(__name__)

# -------------------------------
# Attempt Coinbase Advanced Import
# -------------------------------
try:
    import coinbase_advanced_py as cb
    print("✅ coinbase_advanced_py imported successfully.")
except ModuleNotFoundError as e:
    print("⚠️ coinbase_advanced_py NOT found. Falling back to MockClient.")
    USE_MOCK = True

# -------------------------------
# Coinbase Client Setup
# -------------------------------
if not USE_MOCK and FORCE_LIVE and FORCE_TRADING:
    try:
        API_KEY = os.getenv("COINBASE_API_KEY")
        API_SECRET = os.getenv("COINBASE_API_SECRET")
        client = cb.Client(API_KEY, API_SECRET)
        print("🚀 Live Coinbase client initialized ✅")
    except Exception as e:
        print("❌ Failed to initialize Coinbase client:", e)
        USE_MOCK = True

if USE_MOCK:
    # Minimal MockClient for testing & fallback
    class MockClient:
        def place_order(self, *args, **kwargs):
            print("💤 Mock order executed:", args, kwargs)

    client = MockClient()
    print("⚠️ MockClient initialized (NO LIVE TRADING)")

# -------------------------------
# Flask Routes
# -------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    # Example: execute a trade
    if not USE_MOCK and FORCE_TRADING:
        try:
            client.place_order(**data)
            return jsonify({"status": "live trade executed"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        client.place_order(**data)
        return jsonify({"status": "mock trade executed"})

# -------------------------------
# Run Flask App
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting NIJA Bot Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
