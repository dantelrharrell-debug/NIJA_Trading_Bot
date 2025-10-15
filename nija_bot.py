#!/usr/bin/env python3
import os
import sys
from flask import Flask, jsonify
from dotenv import load_dotenv

# -------------------
# Load environment variables
# -------------------
load_dotenv()
USE_MOCK = os.getenv("USE_MOCK", "False").lower() == "true"

# -------------------
# Coinbase client setup
# -------------------
coinbase_client = None

if not USE_MOCK:
    try:
        import coinbase_advanced_py as cb
        coinbase_client = cb
        print("✅ Imported coinbase_advanced_py")
    except ModuleNotFoundError:
        try:
            import coinbase_advanced as cb
            coinbase_client = cb
            print("✅ Imported coinbase_advanced")
        except ModuleNotFoundError:
            print("❌ Failed to import Coinbase client, falling back to MockClient")
            USE_MOCK = True

# -------------------
# Define MockClient (fallback)
# -------------------
class MockClient:
    def __init__(self):
        print("⚠️ MockClient initialized (no live trading)")

    def get_account(self):
        return {"balance": 0}

    def place_order(self, *args, **kwargs):
        print(f"Mock order executed: args={args}, kwargs={kwargs}")
        return {"id": "mock_order", "args": args, "kwargs": kwargs}

if USE_MOCK or coinbase_client is None:
    coinbase_client = MockClient()

# -------------------
# Flask app setup
# -------------------
app = Flask(__name__)

@app.route("/")
def index():
    return "NIJA Bot is running!"

@app.route("/test_order")
def test_order():
    """
    Place a test order using the coinbase_client (or MockClient).
    """
    result = coinbase_client.place_order(
        product_id="BTC-USD",
        side="buy",
        price="1",
        size="0.001"
    )
    return jsonify({"result": result})

# -------------------
# Debug info (optional)
# -------------------
print("🚀 Starting NIJA Bot")
print("sys.executable:", sys.executable)
print("sys.path:", sys.path)
print("USE_MOCK:", USE_MOCK)

# -------------------
# Start Flask server
# -------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
