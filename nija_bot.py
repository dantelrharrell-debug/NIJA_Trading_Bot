#!/usr/bin/env python3
import os
from pathlib import Path
from flask import Flask
import coinbase_advanced_py as cb

# -------------------------------
# Load API credentials from ENV
# -------------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET_PATH = os.getenv("API_SECRET")  # path to your .pem file

# -------------------------------
# Validate credentials
# -------------------------------
if not API_KEY or not API_SECRET_PATH:
    raise SystemExit("❌ API_KEY or API_SECRET not set")

pem_path = Path(API_SECRET_PATH)
if not pem_path.is_file():
    raise SystemExit(f"❌ PEM file not found at {pem_path}")

# -------------------------------
# Initialize Coinbase Advanced client
# -------------------------------
try:
    client = cb.Client(API_KEY, pem_path)
    print("✅ Coinbase client initialized. LIVE_TRADING=True")
except Exception as e:
    raise SystemExit(f"❌ Failed to initialize Coinbase client: {e}")

# -------------------------------
# Example: get balances
# -------------------------------
try:
    balances = client.get_account_balances()
    print("💰 Starting balances:", balances)
except Exception as e:
    print("⚠️ Error reading balances:", e)

# -------------------------------
# Set live trading flag
# -------------------------------
LIVE_TRADING = True

# -------------------------------
# Initialize Flask app
# -------------------------------
app = Flask(__name__)

@app.route("/")
def index():
    return {"status": "Nija Trading Bot Live!", "LIVE_TRADING": LIVE_TRADING}

# -------------------------------
# Start Flask server
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Starting NIJA Bot Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port)
