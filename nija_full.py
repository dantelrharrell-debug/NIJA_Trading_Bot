import time
import logging
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = Flask(__name__)

class NijaBot:
    def __init__(self, exchange=None):
        """
        exchange: optional ccxt exchange object (Coinbase, Binance, etc.)
        """
        self.exchange = exchange
        logging.info("✅ NijaBot initialized")

    def run_live(self):
        """
        Generator heartbeat to show the bot is running.
        """
        while True:
            logging.info("🔄 NijaBot heartbeat: waiting for webhook trades...")
            time.sleep(5)
            yield None

    def _log_trade(self, trade):
        """
        Cleanly logs trades
        """
        if not trade:
            return

        if isinstance(trade, dict):
            side = (trade.get("side") or trade.get("action") or trade.get("type") or "UNKNOWN").upper()
            symbol = trade.get("symbol") or trade.get("market") or trade.get("pair") or "UNKNOWN"
            price = trade.get("price") or trade.get("exec_price") or trade.get("filled_price") or "?"
            amount = trade.get("amount") or trade.get("size") or trade.get("qty") or "?"
            logging.info(f"✅ Trade executed: {side} {amount} {symbol} @ {price}")

            # Optional: live order execution via CCXT
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
        Handles TradingView webhook JSON
        """
        try:
            trade = data
            self._log_trade(trade)
            return {"status": "success"}
        except Exception as e:
            logging.exception(f"❌ Failed to handle webhook trade: {e}")
            return {"status": "error", "message": str(e)}

# Instantiate bot
nija = NijaBot()

# Flask route for TradingView webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON received"}), 400
    result = nija.handle_webhook(data)
    return jsonify(result)

def start_trading_loop():
    """
    Run the heartbeat generator continuously
    """
    for _ in nija.run_live():
        pass

# Auto-start loop if running this file
if __name__ == "__main__":
    import threading
    threading.Thread(target=start_trading_loop, daemon=True).start()
    logging.info("🚀 NijaBot webhook server starting on port 10000")
    app.run(host="0.0.0.0", port=10000)
