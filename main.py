import os
import time
import logging
import importlib
from threading import Thread
from flask import Flask
from dotenv import load_dotenv

# ------------------------------
# LOGGING
# ------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("nija")

# ------------------------------
# LOAD ENV VARIABLES
# ------------------------------
load_dotenv()
PAPER_MODE = os.getenv("PAPER_MODE", "0") == "1"
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")
TRADEVIEW_WEBHOOK_URL = os.getenv("TRADEVIEW_WEBHOOK_URL")

# ------------------------------
# CRYPTO TICKERS
# ------------------------------
CRYPTO_TICKERS = ["BTC-USD", "ETH-USD", "LTC-USD", "SOL-USD", "XRP-USD", "DOGE-USD"]

# ------------------------------
# ROBUST COINBASE CLIENT IMPORT
# ------------------------------
client = None
ClientClass = None
_import_candidates = [
    "coinbase_advanced_py.client",
    "coinbase_advanced.client",
    "coinbase_advanced_py",
    "coinbase_advanced",
    "coinbase",
    "coinbase.client",
]

if not PAPER_MODE:
    for modname in _import_candidates:
        try:
            spec = importlib.util.find_spec(modname)
            if spec is None:
                continue
            mod = importlib.import_module(modname)
            if hasattr(mod, "Client"):
                ClientClass = getattr(mod, "Client")
            else:
                try:
                    sub = importlib.import_module(modname + ".client")
                    if hasattr(sub, "Client"):
                        ClientClass = getattr(sub, "Client")
                except Exception:
                    pass

            if ClientClass:
                if not COINBASE_API_KEY or not COINBASE_API_SECRET:
                    log.error("Coinbase API key/secret missing; switching to PAPER_MODE.")
                    PAPER_MODE = True
                else:
                    try:
                        client = ClientClass(api_key=COINBASE_API_KEY, api_secret=COINBASE_API_SECRET)
                        log.info("Coinbase client imported from '%s' and initialized.", modname)
                    except Exception as e:
                        log.error("Failed to initialize Coinbase client: %s", e)
                        PAPER_MODE = True
                break
        except Exception as e:
            log.debug("Import candidate '%s' failed: %s", modname, e)
    else:
        log.error("No Coinbase client module found; switching to PAPER_MODE.")
        PAPER_MODE = True
else:
    log.info("PAPER_MODE enabled via environment variable.")

# ------------------------------
# FLASK APP
# ------------------------------
app = Flask(__name__)

@app.route("/")
def health():
    return "Nija Trading Bot Live ✅", 200

# ------------------------------
# TRADE FUNCTIONS
# ------------------------------
def send_tradeview_signal(symbol: str, side: str, quantity: float, price: float):
    if not TRADEVIEW_WEBHOOK_URL:
        return
    trade_data = {
        "symbol": symbol.replace("-", ""),
        "side": side,
        "quantity": quantity,
        "price": price
    }
    try:
        import requests
        response = requests.post(TRADEVIEW_WEBHOOK_URL, json=trade_data, timeout=5)
        if response.status_code == 200:
            log.info("TradeView updated: %s", trade_data)
        else:
            log.warning("TradeView error %s: %s", response.status_code, response.text)
    except Exception as e:
        log.error("TradeView webhook exception: %s", e)

def place_order(symbol: str, side: str, quantity: float, take_profit: float = None, stop_loss: float = None):
    if PAPER_MODE:
        log.info("[PAPER] %s %s units of %s. TP=%s SL=%s", side.upper(), quantity, symbol, take_profit, stop_loss)
        return None

    try:
        order = client.place_order(
            product_id=symbol,
            side=side,
            type="market",
            size=str(quantity)
        )
        price = float(order["price"]) if "price" in order else 0
        log.info("%s order executed for %s: %s", side.upper(), symbol, order)
        send_tradeview_signal(symbol, side, quantity, price)

        # Track TP/SL
        if take_profit or stop_loss:
            Thread(target=monitor_order, args=(symbol, side, quantity, price, take_profit, stop_loss)).start()

        return order
    except Exception as e:
        log.error("Coinbase order failed: %s", e)
        return None

def monitor_order(symbol, side, quantity, entry_price, take_profit=None, stop_loss=None):
    """
    Monitors an open position and closes it when TP/SL levels are hit.
    """
    if PAPER_MODE:
        log.info("[PAPER] Monitoring %s %s, TP=%s, SL=%s", side.upper(), symbol, take_profit, stop_loss)
        return

    while True:
        try:
            ticker = client.get_product_ticker(symbol)
            current_price = float(ticker["price"])
            close = False
            if side.lower() == "buy":
                if take_profit and current_price >= take_profit:
                    close = True
                elif stop_loss and current_price <= stop_loss:
                    close = True
            elif side.lower() == "sell":
                if take_profit and current_price <= take_profit:
                    close = True
                elif stop_loss and current_price >= stop_loss:
                    close = True

            if close:
                # Place market order to close position
                opposite = "sell" if side.lower() == "buy" else "buy"
                client.place_order(
                    product_id=symbol,
                    side=opposite,
                    type="market",
                    size=str(quantity)
                )
                log.info("Position closed for %s: %s units at %s", symbol, quantity, current_price)
                break

        except Exception as e:
            log.error("Error monitoring order for %s: %s", symbol, e)

        time.sleep(5)  # check every 5 seconds

# ------------------------------
# BOT LOOP
# ------------------------------
def run_bot():
    while True:
        for symbol in CRYPTO_TICKERS:
            # Example strategy — replace with your real signals
            place_order(symbol, "buy", 0.001, take_profit=1.05, stop_loss=0.95)
            place_order(symbol, "sell", 0.001, take_profit=0.95, stop_loss=1.05)
            time.sleep(10)

# ------------------------------
# START APP
# ------------------------------
if __name__ == "__main__":
    Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
