#!/usr/bin/env python3
import os
import sys
from flask import Flask
from dotenv import load_dotenv

# ---------------------------
# Load environment
# ---------------------------
load_dotenv()
USE_MOCK = os.getenv("USE_MOCK", "False").lower() == "true"

# ---------------------------
# Coinbase import check
# ---------------------------
coinbase_client = None
if not USE_MOCK:
    try:
        import coinbase_advanced_py as cb
        coinbase_client = cb
        print("✅ Imported coinbase_advanced_py")
    except ModuleNotFoundError:
        print("❌ Coinbase import failed, switching to MockClient")
        USE_MOCK = True

# ---------------------------
# Mock client fallback
# ---------------------------
class MockClient:
    def __init__(self):
        print("⚠️ MockClient initialized (no live trading)")

    def get_account(self):
        return {"balance": 0}

    def place_order(self, *args, **kwargs):
        print(f"Mock order: args={args}, kwargs={kwargs}")
        return {"id": "mock_order"}

if USE_MOCK:
    coinbase_client = MockClient()

# ---------------------------
# Debug info
# ---------------------------
print("sys.executable:", sys.executable)
print("sys.path:", sys.path)

# ---------------------------
# Flask setup
# ---------------------------
app = Flask(__name__)

@app.route("/")
def index():
    return "NIJA Bot is running!"

# ---------------------------
# Start Flask server
# ---------------------------
if __name__ == "__main__":
    print("🚀 Starting NIJA Bot Flask server on port 10000...")
    app.run(host="0.0.0.0", port=10000)
