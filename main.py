import os
import logging
from flask import Flask, request, jsonify
from cbpro import AuthenticatedClient
from pyngrok import ngrok
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

API_KEY = os.getenv("COINBASE_API_KEY")
API_SECRET = os.getenv("COINBASE_API_SECRET")
API_PASSPHRASE = os.getenv("COINBASE_API_PASSPHRASE")

WEBHOOK_SECRET = os.getenv("NIJA_WEBHOOK_SECRET", "supersecrettoken")
LIVE = os.getenv("NIJA_LIVE", "false").lower() == "true"

# Initialize Flask app
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize Coinbase Pro (cbpro2) authenticated client
client = AuthenticatedClient(API_KEY, API_SECRET, API_PASSPHRASE)

# Health check endpoint
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "live": LIVE})

# Status endpoint: shows account balances if live
@app.route("/status", methods=["GET"])
def status():
    if LIVE:
        try:
            accounts = client.get_accounts()
            return jsonify({"status": "live", "accounts": accounts})
        except Exception as e:
            logging.error(f"Error fetching accounts: {e}")
            return jsonify({"status": "error", "message": str(e)})
    else:
        return jsonify({"status": "offline"})

# Webhook endpoint for TradingView alerts
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("X-WEBHOOK-TOKEN") != WEBHOOK_SECRET:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    data = request.json
    logging.info(f"Received webhook: {data}")

    if LIVE:
        # Example: simple market order
        if data.get("action") == "buy":
            try:
                order = client.place_market_order(
                    product_id=data["symbol"],
                    side="buy",
                    funds=data.get("funds", "10")  # default $10
                )
                logging.info(f"Order executed: {order}")
            except Exception as e:
                logging.error(f"Order error: {e}")
        elif data.get("action") == "sell":
            try:
                order = client.place_market_order(
                    product_id=data["symbol"],
                    side="sell",
                    funds=data.get("funds", "10")
                )
                logging.info(f"Order executed: {order}")
            except Exception as e:
                logging.error(f"Order error: {e}")

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
