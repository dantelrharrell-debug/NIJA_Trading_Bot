#!/usr/bin/env python3
import os
import sys
from flask import Flask, request, jsonify

# --------------------------
# Ensure local .venv is in path
# --------------------------
venv_site_packages = os.path.join(os.path.dirname(__file__), ".venv/lib/python3.11/site-packages")
if venv_site_packages not in sys.path:
    sys.path.insert(0, venv_site_packages)

# --------------------------
# Flask app setup
# --------------------------
app = Flask(__name__)

WEBHOOK_SECRET = os.getenv("TV_WEBHOOK_SECRET", "change_this_secret")

# --------------------------
# Determine live vs mock mode
# --------------------------
USE_MOCK = os.getenv("USE_MOCK", "False").lower() == "true"

if not USE_MOCK:
    try:
        import coinbase_advanced_py as cap
        print("✅ coinbase_advanced_py imported successfully.")
        # Load API keys
        API_KEY = os.getenv("API_KEY")
        API_SECRET = os.getenv("API_SECRET")
        API_PEM_B64 = os.getenv("API_PEM_B64")
        # Initialize live client
        client = cap.CoinbaseAdvancedClient(api_key=API_KEY, api_secret=API_SECRET, api_pem_b64=API_PEM_B64)
    except ModuleNotFoundError:
        print("❌ coinbase_advanced_py import failed! Using MockClient.")
        USE_MOCK = True

if USE_MOCK:
    class MockClient:
        def place_order(self, *args, **kwargs):
            print("⚠️ Mock order executed:", args, kwargs)
            return {"status": "mocked"}

    client = MockClient()
    print("⚠️ MockClient active. No live trading.")

# --------------------------
# Webhook route
# --------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    secret = request.headers.get("X-WEBHOOK-SECRET") or data.get("secret")
    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 401

    # Example: execute order if 'buy' key exists
    if "buy" in data:
        order = client.place_order(symbol=data["buy"], side="buy", quantity=data.get("qty", 1))
        return jsonify({"status": "success", "order": order})

    return jsonify({"status": "ignored"}), 200

# --------------------------
# Root health check
# --------------------------
@app.route("/")
def root():
    return "Nija Bot is running! ✅"

# --------------------------
# Run Flask app
# --------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
