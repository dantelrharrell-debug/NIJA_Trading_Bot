#!/usr/bin/env python3
import os
import logging
from flask import Flask, request, jsonify

# -------------------
# Logging
# -------------------
logger = logging.getLogger("nija_bot")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# -------------------
# Flask app
# -------------------
app = Flask(__name__)

# -------------------
# Coinbase client setup
# -------------------
USE_MOCK = False  # always live

try:
    import coinbase_advanced_py as cb
    logger.info("✅ Imported coinbase_advanced_py successfully")
except ImportError as e:
    logger.critical("❌ Failed to import coinbase_advanced_py: %s", e)
    raise e  # stop startup if live client is missing

# -------------------
# Load API keys from environment
# -------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM_B64 = os.getenv("API_PEM_B64")

if not all([API_KEY, API_SECRET, API_PEM_B64]):
    logger.critical("❌ Missing one or more Coinbase API credentials in environment variables")
    raise ValueError("Missing Coinbase API credentials")

# Initialize Coinbase client
client = cb.CoinbaseAdvanced(
    api_key=API_KEY,
    api_secret=API_SECRET,
    api_pem_b64=API_PEM_B64
)
logger.info("✅ Coinbase client initialized successfully")

# -------------------
# Simple health check
# -------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "live", "mock": USE_MOCK})

# -------------------
# Example webhook route
# -------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    logger.info("Webhook received: %s", data)
    return jsonify({"status": "ok"}), 200

# -------------------
# Run app via gunicorn in Render
# -------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
