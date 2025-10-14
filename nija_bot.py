#!/usr/bin/env python3
import os
import sys
import traceback
from flask import Flask

# -------------------
# Determine mock mode
# -------------------
USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"

if not USE_MOCK:
    try:
        import coinbase_advanced_py as cb
        print("✅ coinbase_advanced_py imported successfully.")
        # Load API keys
        API_KEY = os.getenv("API_KEY")
        API_SECRET = os.getenv("API_SECRET")
        if not API_KEY or not API_SECRET:
            raise ValueError("❌ Missing Coinbase API_KEY or API_SECRET")
        client = cb.Client(API_KEY, API_SECRET)
        print("🚀 Coinbase client ready")
    except Exception as e:
        print("❌ Failed to load Coinbase client, switching to mock mode.")
        traceback.print_exc()
        USE_MOCK = True

if USE_MOCK:
    print("⚠️ Running in mock mode — Coinbase client not connected.")
    client = None  # Mock client placeholder

# -------------------
# Live trading flag
# -------------------
LIVE_TRADING = True if not USE_MOCK else False
print(f"🟢 NIJA BOT starting; LIVE_TRADING = {LIVE_TRADING}")

# -------------------
# Flask setup
# -------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "NIJA Bot is running! 🚀"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
