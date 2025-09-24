import time
import logging
import os
import importlib
import requests
from flask import Flask
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("nija")

PAPER_MODE = os.getenv("PAPER_MODE", "0") == "1"
TRADEVIEW_WEBHOOK_URL = os.getenv("TRADEVIEW_WEBHOOK_URL", "").strip()

TRADING_PLAN = {
    "LTC-USD": {"qty": 0.05, "profit_pct": 1.5, "stop_pct": 0.5},
    "SOL-USD": {"qty": 0.1, "profit_pct": 2.0, "stop_pct": 1.0},
    "XRP-USD": {"qty": 50, "profit_pct": 1.2, "stop_pct": 0.5},
    "DOGE-USD": {"qty": 100, "profit_pct": 1.0, "stop_pct": 0.3},
    "ETH-USD": {"qty": 0.01, "profit_pct": 1.5, "stop_pct": 0.7},
    "BTC-USD": {"qty": 0.001, "profit_pct": 1.0, "stop_pct": 0.5},
}

CRYPTO_TICKERS = list(TRADING_PLAN.keys())

# ---------------------------
# Coinbase Client Init
# ---------------------------
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")

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
                        mod = sub
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
                        log.error("Client init failed for %s: %s", modname, e)
                        client = None
                        PAPER_MODE = True
                break
        except Exception as e:
            log.debug("Import candidate '%s' failed: %s", modname, e)
    else:
        log.error("No Coinbase client found. Switching to PAPER_MODE.")
        PAPER_MODE = True
else:
    log.info("PAPER_MODE enabled via environment variable.")

# ---------------------------
# PLACE ORDER
# ---------------------------
def place_order_safe(symbol: str, side: str, qty: float):
    if PAPER_MODE:
        fake_price = round(1000 * (1 + (hash(symbol) % 100)/10000.0), 2)
        fake_id = f"paper-{int(time.time())}"
        log.info(f"[PAPER] {side.upper()} {symbol} x{qty} @ {fake_price} (id={fake_id})")
        return {"success": True, "result": {"id": fake_id, "price": fake_price, "size": qty}}

    if client is None:
        err = "Coinbase client not initialized"
        log.error(err)
        return {"success": False, "error": err}

    try:
        res = client.place_order(
            product_id=symbol,
            side=side.lower(),
            type="market",
            size=str(qty)
        )
        log.info("Placed LIVE order: %s %s x%s -> %s", side.upper(), symbol, qty, res)
        return {"success": True, "result": res}
    except Exception as e:
        log.error("Live order failed for %s %s x%s: %s", side, symbol, qty, e)
        return {"success": False, "error": str(e)}

# ---------------------------
# POSITIONS
# ---------------------------
positions = {}

# ---------------------------
# TECHNICAL STRATEGY (MA + RSI)
# ---------------------------
import pandas as pd

def calculate_ma_rsi(prices, ma_period=10, rsi_period=14):
    df = pd.DataFrame({"close": prices})
    df["ma"] = df["close"].rolling(ma_period).mean()
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(rsi_period).mean()
    avg_loss = loss.rolling(rsi_period).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df["rsi"] = 100 - (100 / (1 + rs))
    return df["ma"].iloc[-1], df["rsi"].iloc[-1]

# ---------------------------
# FETCH PRICE HISTORY
# ---------------------------
def get_price_history(symbol, limit=50):
    if PAPER_MODE:
        return [1000 + i for i in range(limit)]
    else:
        try:
            data = client.get_product_historic_rates(symbol, granularity=60)
            prices = [float(x[4]) for x in data]  # closing prices
            return prices[-limit:]
        except Exception as e:
            log.error("Failed to fetch price history for %s: %s", symbol, e)
            return [1000 + i for i in range(limit)]

# ---------------------------
# DETERMINE TRADE SIGNAL
# ---------------------------
def get_trade_signal(symbol):
    prices = get_price_history(symbol)
    ma, rsi = calculate_ma_rsi(prices)
    current_price = prices[-1]
    log.info("Symbol %s: current=%.2f, MA=%.2f, RSI=%.2f", symbol, current_price, ma, rsi)

    # Simple rule:
    # Long: price above MA and RSI < 70
    # Short: price below MA and RSI > 30
    if current_price > ma and rsi < 70:
        return "buy"
    elif current_price < ma and rsi > 30:
        return "sell"
    else:
        return None

# ---------------------------
# CHECK AND CLOSE POSITIONS
# ---------------------------
def check_position(symbol: str, current_price: float):
    pos = positions.get(symbol)
    if not pos:
        return
    plan = TRADING_PLAN[symbol]
    entry_price = pos["entry_price"]
    qty = pos["qty"]

    if pos["type"] == "long":
        profit_target = entry_price * (1 + plan["profit_pct"]/100)
        stop_loss = entry_price * (1 - plan["stop_pct"]/100)
        if current_price >= profit_target or current_price <= stop_loss:
            log.info("Closing long %s: entry %.2f, current %.2f", symbol, entry_price, current_price)
            place_order_safe(symbol, "sell", qty)
            positions.pop(symbol)
    elif pos["type"] == "short":
        profit_target = entry_price * (1 - plan["profit_pct"]/100)
        stop_loss = entry_price * (1 + plan["stop_pct"]/100)
        if current_price <= profit_target or current_price >= stop_loss:
            log.info("Closing short %s: entry %.2f, current %.2f", symbol, entry_price, current_price)
            place_order_safe(symbol, "buy", qty)
            positions.pop(symbol)

# ---------------------------
# MAIN BOT LOOP
# ---------------------------
def run_bot():
    while True:
        for symbol in CRYPTO_TICKERS:
            plan = TRADING_PLAN[symbol]
            qty = plan["qty"]

            # get current price
            if PAPER_MODE:
                current_price = round(1000 * (1 + (hash(symbol) % 100)/10000.0), 2)
            else:
                ticker = client.get_product_ticker(symbol)
                current_price = float(ticker.get("price", 1000))

            # Check and close TP/SL positions
            check_position(symbol, current_price)

            # Open new position if none
            if symbol not in positions:
                signal = get_trade_signal(symbol)
                if signal:
                    res = place_order_safe(symbol, signal, qty)
                    if res["success"]:
                        positions[symbol] = {"type": "long" if signal=="buy" else "short",
                                             "entry_price": current_price,
                                             "qty": qty}
                        log.info("Opened %s %s x%s @ %.2f", positions[symbol]["type"], symbol, qty, current_price)

            time.sleep(2)

# ---------------------------
# FLASK APP
# ---------------------------
app = Flask(__name
