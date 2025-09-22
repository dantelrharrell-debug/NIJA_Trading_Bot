import os
from flask import Flask, request, jsonify
# OLD:
# from cbpro import AuthenticatedClient

# NEW:
from cbpro2 import AuthenticatedClient
from pyngrok import ngrok
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")
COINBASE_API_PASSPHRASE = os.getenv("COINBASE_API_PASSPHRASE")
NIJA_WEBHOOK_SECRET = os.getenv("NIJA_WEBHOOK_SECRET", "supersecrettoken")
LIVE = os.getenv("NIJA_LIVE", "false").lower() == "true"

app = Flask(__name__)

# Initialize Coinbase Pro client
client = AuthenticatedClient(
    key=COINBASE_API_KEY,
    secret=COINBASE_API_SECRET,
    passphrase=COINBASE_API_PASSPHRASE,
    api_url="https://api.pro.coinbase.com"
)

# Optional: expose local server through ngrok for testing
if not LIVE:
    public_url = ngrok.connect(5000)
    print(f" * ngrok tunnel running -> {public_url}")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/webhook", methods=["POST"])
def webhook():
    # Verify secret
    if request.headers.get("X-NIJA-WEBHOOK") != NIJA_WEBHOOK_SECRET:
        return jsonify({"error": "unauthorized"}), 401

    data = request.json
    print("Received webhook:", data)

    # Example: trading logic placeholder
    if data.get("action") == "buy":
        # client.place_order(...)  # Add your buy logic here
        print("Buy signal received")
    elif data.get("action") == "sell":
        # client.place_order(...)  # Add your sell logic here
        print("Sell signal received")

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
