import os
import logging
from flask import Flask, request, jsonify
import threading
import ccxt

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# -------------------------------
# Flask App
# -------------------------------
app = Flask(__name__)

# -------------------------------
# NijaBot Class
# -------------------------------
class NijaBot:
    def __init__(self):
        # Load Coinbase API keys from environment
        self.api_key = os.getenv("COINBASE_API_KEY")
        self.secret = os.getenv("COINBASE_SECRET")
        self.exchange = None

        if self.api_key and self.secret:
            try:
                self.exchange = ccxt.coinbasepro({
                    'apiKey': self.api_key,
                    'secret': self.secret,
                    'enableRateLimit': True,
                })
                logging.info("✅ Coinbase exchange initialized.")
            except Exception as e:
                logging.error(f"❌ Failed to initialize Coinbase: {e}")
        else:
            logging.error("❌ Coinbase API keys not found. Set COINBASE_API_KEY and COINBASE_SECRET in .env")

    # Place live trade
    def place_trade(self, symbol, side, amount):
        if self.exchange:
            # Convert symbol to Coinbase format
            symbol = symbol.replace("/", "-")
            try:
                order = self.exchange.create_market_order(symbol, side.lower(), float(amount))
                logging.info(f"🚀 Order placed on Coinbase: {order}")
                return order
            except Exception as e:
                logging.error(f"❌ Failed to place order {side} {amount} {symbol}: {e}")
        else:
            logging.error("❌ Exchange not initialized. Cannot place order.")

    # Handle incoming webhook trade
    def handle_webhook(self, data):
        logging.info(f"Webhook received: {data}")

        # Check if single trade object or list of trades
        trades = data if isinstance(data, list) else [data]

        for trade in trades:
            symbol = trade.get("symbol")
            side = trade.get("side")
            amount = trade.get("amount")

            if not all([symbol, side, amount]):
                logging.error(f"❌ Invalid trade object: {trade}")
                continue

            logging.info(f"📈 Executing trade: {side.upper()} {amount} {symbol}")
            self.place_trade(symbol, side, amount)


# -------------------------------
# Initialize Bot
# -------------------------------
nija = NijaBot()


# -------------------------------
# Webhook Route
# -------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        nija.handle_webhook(data)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logging.error(f"❌ Webhook processing failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


# -------------------------------
# Start Trading Loop (background)
# -------------------------------
def start_trading_loop():
    logging.info("🚀 Nija Trading Bot live. Waiting for webhooks at /webhook")
    # The bot now waits for webhooks, so this loop just keeps Flask alive
    threading.Event().wait()


# -------------------------------
# Run Flask
# -------------------------------
if __name__ == "__main__":
    threading.Thread(target=start_trading_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
