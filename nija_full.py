import time
import logging
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = Flask(__name__)

class NijaBot:
    def __init__(self, exchange=None):
        """
        exchange: optional initialized ccxt exchange (Coinbase, Binance, etc.)
        """
        self.exchange = exchange
        logging.info("✅ NijaBot initialized")

    def run_live(self):
        """
        Generator placeholder if you want to iterate over live events
        """
        while True:
            logging.info("🔄 NijaBot heartbeat: waiting for webhook trades...")
            time.sleep(5)
            yield None

    def _log_trade(self, trade):
        """
        Logs trades in a clean format
        """
        if not trade:
            return

        if isinstance(trade, dict):
            side = (trade.get("side") or trade.get("action") or trade.get("type") or "UNKNOWN").upper()
            symbol = trade.get("symbol") or trade.get("market") or trade.get("pair") or "UNKNOWN"
            price = trade.get("price") or trade.get("exec_price") or trade.get("filled_price") or "?"
            amount = trade.get("amount") or trade.get("size") or trade.get("qty") or "?"
            logging.info(f"✅ Trade executed: {side} {amount} {symbol} @ {price}")

            # Optional: execute on CCXT exchange
            # if self.exchange:
            #     try:
            #         order = self.exchange.create_market_order(symbol, side.lower(), amount)
            #         logging.info(f"✅ Order placed on exchange: {order}")
            #     except Exception as e:
            #         logging.error(f"❌ Failed to place order: {e}")
        else:
            logging.info(f"✅ Trade event: {trade}")

    def handle_webhook(self, data):
        """
        Call this with JSON payload from TradingView webhook
        Expected keys: 'side', 'symbol', 'price', 'amount'
        """
        try:
            trade = data
            self._log_trade(trade)
            return {"status": "success"}
        except Exception as e:
            logging.exception(f"❌ Failed to handle webhook trade: {e}")
            return {"status": "error", "message": str(e)}

# Instantiate the bot
nija = NijaBot()

# Flask route to handle TradingView webhooks
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "No JSON received"}), 400
        result = nija.handle_webhook(data)
        return jsonify(result)
    return jsonify({"status": "error", "message": "Invalid method"}), 405

def start_trading(nija_instance=None):
    """
    Optional generator-based loop to run alongside webhook server
    """
    bot = nija_instance or nija
    try:
        for trade in bot.run_live():
            if trade is None:
                continue
    except Exception as e:
        logging.exception(f"Trading loop crashed: {e}")

# If running this file directly, start Flask + optional loop
if __name__ == "__main__":
    import threading
    threading.Thread(target=start_trading, args=(nija,), daemon=True).start()
    logging.info("🚀 Starting NijaBot webhook server on port 10000")
    app.run(host="0.0.0.0", port=10000)
