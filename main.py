import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from coinbase_advancedtrade.client import Client


# Load environment variables from .env locally or Render
load_dotenv()
API_KEY = os.getenv("COINBASE_API_KEY")
API_SECRET = os.getenv("COINBASE_API_SECRET")

# Initialize Coinbase client
client = Client(api_key=API_KEY, api_secret=API_SECRET)

# Create Flask app
app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/status", methods=["GET"])
def status():
    try:
        accounts = client.get_accounts()
        return jsonify({"status": "connected", "accounts": accounts})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    try:
        symbol = data.get("symbol")
        action = data.get("action")
        size = data.get("size")

        if action == "buy":
            order = client.place_order(
                product_id=symbol,
                side="buy",
                size=size,
                type="market"
            )
        elif action == "sell":
            order = client.place_order(
                product_id=symbol,
                side="sell",
                size=size,
                type="market"
            )
        else:
            return jsonify({"status": "ignored", "message": "Unknown action"}), 400

        return jsonify({"status": "success", "order": order})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Use Render port if available, otherwise default to 5000 locally
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
