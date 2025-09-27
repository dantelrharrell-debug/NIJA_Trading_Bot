from nija_full import nija, app, start_trading_loop
import threading
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Start the trading loop in a background thread
threading.Thread(target=start_trading_loop, daemon=True).start()

logging.info("🚀 Nija Trading Bot live. Listening for webhooks at /webhook")

if __name__ == "__main__":
    # Start the Flask server
    app.run(host="0.0.0.0", port=10000)
