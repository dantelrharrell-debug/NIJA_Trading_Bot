import os
import json
import logging
from flask import Flask, request, jsonify
import ccxt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ======== Initialize Coinbase Client (Spot & Futures) ========
try:
    coinbase_client = ccxt.coinbase({
        'apiKey': os.getenv("COINBASE_SPOT_KEY"),
        'secret': os.getenv("COINBASE_SPOT_SECRET"),
        'password': os.getenv("COINBASE_SPOT_PASSPHRASE"),
    })
    coinbase_client.load_markets()
    logging.info("✅ Coinbase Spot & Futures client initialized")
except Exception as e:
    logging.exception("❌ Coinbase client failed to initialize: %s", e)

#
            results.append({"symbol": symbol, "side": side, "amount": amount, "status": "auth_failed", "error": str(e)})
        except Exception as e:
            logging.exception("❌ Order failed")
            results.append({"symbol": symbol, "side": side, "amount": amount, "status": "error", "error": str(e)})

    return jsonify({"ok": True, "results": results}), 200

# ======== Health Check ========
@app.route("/", methods=["GET"])
def index():
    return "NijaBot is live! 🚀", 200

# ======== Run Flask ========
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logging.info(f"Starting NijaBot on port {port}")
    app.run(host="0.0.0.0", port=port)
 ======== Webhook Route ========
@app.route("/webhook", methods=["POST"])
def webhook():
    logging.info("---- WEBHOOK RECEIVED ----")
    headers = dict(request.headers)
    raw_body = request.get_data(as_text=True)
    logging.info("Headers: %s", headers)
    logging.info("Raw body: %s", raw_body)

    # Optional: Verify webhook secret
    secret = os.getenv("TRADINGVIEW_WEBHOOK_SECRET")
    if secret and headers.get("Tradingview-Webhook-Secret") != secret:
        logging.warning("❌ Webhook secret mismatch")
        return jsonify({"ok": False, "error": "webhook secret mismatch"}), 400

    # Parse JSON (handles double-encoded JSON)
    try:
        data = request.get_json(silent=True)
        if data is None:
            parsed_once = json.loads(raw_body)
            if isinstance(parsed_once, str):
                data = json.loads(parsed_once)
            else:
                data = parsed_once
    except Exception as e:
        logging.exception("❌ JSON parse failed")
        return jsonify({"ok": False, "error": "invalid JSON", "details": str(e)}), 400

    logging.info("Parsed JSON: %s", data)

    # Normalize payload to list of orders
    orders = data if isinstance(data, list) else [data]

    # Validate required fields
    required_keys = {"symbol", "side", "amount"}
    for order in orders:
        if not isinstance(order, dict):
            return jsonify({"ok": False, "error": "order not a JSON object"}), 400
        missing = list(required_keys - set(order.keys()))
        if missing:
            return jsonify({"ok": False, "error": "missing required fields", "missing": missing}), 400

    # ======== Execute Orders ========
    results = []
    for order in orders:
        symbol = order["symbol"]
        side = order["side"].lower()
        amount = float(order["amount"])
        market_type = order.get("market", "spot").lower()  # default to spot

        try:
            logging.info("Placing %s order for %s %s", side, amount, symbol)
            resp = coinbase_client.create_order(symbol, "market", side, amount)
            results.append({
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "status": "success",
                "exchange_resp": resp
            })
        except ccxt.AuthenticationError as e:
            logging.exception("❌ Authentication failed")
