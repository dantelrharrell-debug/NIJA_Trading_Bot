import shim_requests_packages_six   # must be the very first import
import collections_fix              # keep this just after shim

import os
import logging
from flask import Flask, request, jsonify
from pyngrok import ngrok
from cbpro2 import AuthenticatedClient
from dotenv import load_dotenv

# --- Flask app ---
app = Flask(__name__)

# --- Coinbase client ---
client = AuthenticatedClient(
    key=os.getenv("COINBASE_API_KEY"),
    b64secret=os.getenv("COINBASE_API_SECRET"),
    passphrase=os.getenv("COINBASE_API_PASSPHRASE")
)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "live": os.getenv("NIJA_LIVE", "false")})

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    token = data.get("token", "")
    
    if token != os.getenv("NIJA_WEBHOOK_SECRET", "supersecrettoken"):
        return jsonify({"error": "Invalid token"}), 403

    action = data.get("action")
    symbol = data.get("symbol")
    size = data.get("size")

    print("Webhook received:", data)

    if os.getenv("NIJA_LIVE", "false").lower() == "true":
        try:
            if action.lower() == "buy":
                order = client.place_market_order(
                    product_id=symbol,
                    side="buy",
                    size=str(size)
                )
            elif action.lower() == "sell":
                order = client.place_market_order(
                    product_id=symbol,
                    side="sell",
                    size=str(size)
                )
            else:
                return jsonify({"error": "Unknown action"}), 400

            print("Order executed:", order)
            return jsonify({"status": "success", "order": order})
        except Exception as e:
            print("Error placing order:", e)
            return jsonify({"error": str(e)}), 500
    else:
        print("NIJA_LIVE=false → no trade executed")
        return jsonify({"status": "ok", "message": "Test mode, trade not executed", "data": data})

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
