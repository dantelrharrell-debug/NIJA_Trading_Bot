#!/usr/bin/env python3
import os
import sys
import traceback
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# ------------------------
# Load environment variables
# ------------------------
load_dotenv()  # Loads variables from a .env file if present

# ------------------------
# Debug: list installed packages
# ------------------------
site_packages_path = os.path.join(os.path.dirname(sys.executable), "lib/python3.11/site-packages")
print("Installed packages:", os.listdir(site_packages_path))

# ------------------------
# Flask app setup
# ------------------------
app = Flask(__name__)

# ------------------------
# Webhook secret
# ------------------------
WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")
    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 401
    # Your webhook logic here
    return jsonify({"status": "ok"}), 200

# ------------------------
# Coinbase client setup
# ------------------------
USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"

if not USE_MOCK:
    try:
        import coinbase_advanced_py as cb
        print("✅ coinbase_advanced_py imported successfully.")

        # Load API keys from environment variables
        API_KEY = os.getenv("API_KEY")
        API_SECRET = os.getenv("API_SECRET")
        API_PEM_B64 = os.getenv("API_PEM_B64")

        client = cb.CoinbaseAdvancedClient(
            api_key=API_KEY,
            api_secret=API_SECRET,
            api_pem_b64=API_PEM_B64
        )
        print("✅ Coinbase client initialized.")
    except Exception as e:
        print("❌ Coinbase client setup failed:", e)
else:
    print("⚠️ Running in MOCK mode, no live trades.")

# ------------------------
# App entry point
# ------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
