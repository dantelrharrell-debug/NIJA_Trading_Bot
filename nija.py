import time
import logging
import ccxt
from flask import Flask, request, jsonify

# -----------------------------
# Logging Setup (console + file)
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("trades.log"),   # logs to file
        logging.StreamHandler()              # logs to console
    ]
)

app = Flask(__name__)

class NijaBot:
    def __init__(self, api_key, api_secret):
        # Initialize CoinbasePro exchange via CCXT
        self.exchange = ccxt.coinbasepro({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
        logging.info("✅ NijaBot initialized with CoinbasePro")

    def run_live(self):
        """Generator heartbeat to show the bot is running."""
        while True:
            logging.info("🔄 NijaBot heartbeat: waiting for webhook trades...")
            time.sleep(5)
            yield None

    def _log_trade(self, trade):
        """Logs trades and places them on Coinbase"""
        if not trade or not isinstance(trade, dict):
            logging.info(f"✅ Trade event: {trade}")
            return

        side = (trade.get("side") or trade.get("action") or trade.get("type") or "UNKNOWN").upper()
        symbol = trade.get("symbol") or trade.get("market") or trade.get("pair") or "UNKNOWN"
        price = trade.get("price") or trade.get("exec_price") or trade.get("filled_price") or "?"
        amount = trade.get("amount") or trade.get("size") or trade.get("qty") or "?"

        message = f"✅ Trade executed: {side} {amount} {symbol} @ {price}"
        logging.info(message)

        # Live execution on Coinbase
        if self.exchange:
            try:
                # Coinbase expects lowercase side
                order = self.exchange.create_market_order(symbol, side.lower(), float(amount))
                logging.info(f"🚀 Order placed on Coinbase: {order}")
            except Exception as e:
                logging.error(f"❌ Failed to place order: {e}")

    def handle_webhook(self, data):
        """Handles TradingView webhook JSON"""
        try:
            trade = data
            self._log_trade(trade)
            return {"status": "success"}
        except Exception as e:
            logging.exception(f"❌ Failed to handle webhook trade: {e}")
            return {"status": "error", "message": str(e)}

# Instantiate bot with your Coinbase credentials
import os
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_SECRET = os.getenv("COINBASE_SECRET")
nija = NijaBot(COINBASE_API_KEY, COINBASE_SECRET)

# Flask route for TradingView webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON received"}), 400
    result = nija.handle_webhook(data)
    return jsonify(result)

def start_trading_loop():
    """Run the heartbeat generator continuously"""
    for _ in nija.run_live():
        pass

# Auto-start loop if running this file directly
if __name__ == "__main__":
    import threading
    threading.Thread(target=start_trading_loop, daemon=True).start()
    logging.info("🚀 NijaBot webhook server starting on port 10000")
    app.run(host="0.0.0.0", port=10000)
