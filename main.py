import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("nija")

PAPER_MODE = os.getenv("PAPER_MODE", "0") == "1"
client = None

if not PAPER_MODE:
    try:
        from coinbase_advanced_py.client import Client
        COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
        COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")
        client = Client(api_key=COINBASE_API_KEY, api_secret=COINBASE_API_SECRET)
        log.info("coinbase-advanced-py imported and client initialized.")
    except ModuleNotFoundError as mnfe:
        log.error("coinbase-advanced-py not installed. Switching to PAPER_MODE. Error: %s", mnfe)
        PAPER_MODE = True
    except Exception as e:
        log.error("Failed to initialize Coinbase client, switching to PAPER_MODE. Error: %s", e)
        PAPER_MODE = True
else:
    log.info("PAPER_MODE enabled via environment variable.")
import os
import time
import requests
from coinbase_advanced_py.client import Client
from dotenv import load_dotenv
from flask import Flask

# ------------------------------
# LOAD ENV VARIABLES
# ------------------------------
load_dotenv()

COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")
TRADEVIEW_WEBHOOK_URL = os.getenv("TRADEVIEW_WEBHOOK_URL")

CRYPTO_TICKERS = ["BTC-USD", "ETH-USD"]  # Add more as needed

client = Client(api_key=COINBASE_API_KEY, api_secret=COINBASE_API_SECRET)
app = Flask(__name__)

# ------------------------------
# FUNCTIONS
# ------------------------------
def place_coinbase_order(symbol: str, side: str, quantity: float):
    try:
        order = client.place_order(
            product_id=symbol,
            side=side,
            type="market",
            size=str(quantity)
        )
        print(f"Coinbase {side} order executed:", order)
        send_tradeview_signal(symbol, side, quantity, float(order['fill_fees']))
        return order
    except Exception as e:
        print("Coinbase order failed:", e)
        return None

def send_tradeview_signal(symbol: str, side: str, quantity: float, price: float):
    trade_data = {
        "symbol": symbol.replace("-", ""),
        "side": side,
        "quantity": quantity,
        "price": price
    }
    try:
        response = requests.post(TRADEVIEW_WEBHOOK_URL, json=trade_data, timeout=5)
        if response.status_code == 200:
            print("TradeView updated:", trade_data)
        else:
            print("TradeView error:", response.status_code, response.text)
    except Exception as e:
        print("TradeView webhook exception:", e)

# ------------------------------
# FLASK HEALTH CHECK
# ------------------------------
@app.route("/")
def health():
    return "Nija Trading Bot Live ✅", 200

# ------------------------------
# MAIN LOOP
# ------------------------------
def run_bot():
    while True:
        for symbol in CRYPTO_TICKERS:
            # Example trade logic — replace with your strategy
            place_coinbase_order(symbol, side="buy", quantity=0.001)
            time.sleep(10)  # Adjust for strategy timing

if __name__ == "__main__":
    from threading import Thread
    Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
