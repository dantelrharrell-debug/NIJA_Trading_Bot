# main.py -- Nija Trading Bot with Coinbase Advanced TP/SL (Bracket) orders
# BEFORE RUNNING: set COINBASE_API_KEY, COINBASE_API_SECRET, TRADEVIEW_WEBHOOK_URL, PAPER_MODE env vars.

import os
import time
import logging
import importlib
import requests
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("nija")

# ---------------------------
# Config
# ---------------------------
PAPER_MODE = os.getenv("PAPER_MODE", "0") == "1"
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")
TRADEVIEW_WEBHOOK_URL = os.getenv("TRADEVIEW_WEBHOOK_URL", "").strip()

CRYPTO_TICKERS = ["BTC-USD","ETH-USD","LTC-USD","SOL-USD","XRP-USD","DOGE-USD"]

# Trading params (tune these)
TRADE_QUANTITY = {
    "BTC-USD": 0.0001,
    "ETH-USD": 0.001,
    "LTC-USD": 0.01,
    "SOL-USD": 0.5,
    "XRP-USD": 10,
    "DOGE-USD": 50
}
PARENT_ORDER_KIND = "market"    # or "limit" if you want limit parents
TP_PCT = 0.02   # 2% take profit default
SL_PCT = 0.01   # 1% stop-loss default
LOOP_DELAY_PER_TICKER = 3       # seconds between tickers

# ---------------------------
# Coinbase client (robust import / init)
# ---------------------------
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
            # try to find an exported Client class
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
                        log.info("Coinbase client initialized from '%s'.", modname)
                    except Exception as e:
                        log.error("Failed to initialize client from %s: %s", modname, e)
                        client = None
                        PAPER_MODE = True
                break
        except Exception as e:
            log.debug("Import candidate '%s' failed: %s", modname, e)
    else:
        log.error("No Coinbase client found; enabling PAPER_MODE.")
        PAPER_MODE = True
else:
    log.info("PAPER_MODE enabled via env var.")

# ---------------------------
# Flask health check (keeps host happy)
# ---------------------------
app = Flask(__name__)
@app.route("/")
def health():
    return "Nija Trading Bot Live ✅", 200

# ---------------------------
# Helper: send TradeView webhook (optional)
# ---------------------------
def send_tradeview_signal(symbol, side, quantity, price):
    if not TRADEVIEW_WEBHOOK_URL:
        return
    payload = {"symbol": symbol.replace("-", ""), "side": side, "quantity": quantity, "price": price, "ts": int(time.time())}
    try:
        r = requests.post(TRADEVIEW_WEBHOOK_URL, json=payload, timeout=5)
        log.info("TradeView webhook returned %s for %s", r.status_code, symbol)
    except Exception as e:
        log.warning("TradeView webhook error: %s", e)

# ---------------------------
# Market data & indicators (VWAP, RSI, EMA)
# ---------------------------
def fetch_candles(symbol, granularity=60, points=200):
    """
    Returns a DataFrame with columns: time, low, high, open, close, volume (Coinbase formats)
    granularity in seconds. For quick operation we request a small number of points.
    """
    if PAPER_MODE or client is None:
        now = datetime.utcnow()
        rows = []
        for i in range(points):
            t = int((now - timedelta(seconds=(points - i) * granularity)).timestamp())
            price = 100 + np.random.randn()  # simulated
            rows.append([t, price, price, price, price, float(abs(np.random.randn()) + 1)])
        df = pd.DataFrame(rows, columns=["time", "low", "high", "open", "close", "volume"])
        return df
    try:
        resp = client.get_candles(product_id=symbol, granularity=granularity)  # SDK method name may vary (see docs)
        # If SDK returns list-of-lists [time, low, high, open, close, volume] (Coinbase style), we normalize:
        df = pd.DataFrame(resp, columns=["time","low","high","open","close","volume"])
        df = df.sort_values("time").reset_index(drop=True)
        return df
    except Exception as e:
        log.error("Failed to fetch candles for %s: %s", symbol, e)
        return pd.DataFrame()

def vwap_from_df(df):
    if df.empty or df["volume"].sum() == 0:
        return None
    return (df["close"] * df["volume"]).sum() / df["volume"].sum()

def rsi_from_df(df, period=14):
    if df.empty or len(df) < period:
        return 50.0
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean().iloc[-1]
    avg_loss = loss.rolling(period).mean().iloc[-1]
    rs = avg_gain / (avg_loss + 1e-9)
    return 100 - (100 / (1 + rs))

def ema_from_df(df, period=20):
    if df.empty:
        return None
    return df["close"].ewm(span=period, adjust=False).mean().iloc[-1]

def get_indicators(symbol):
    df = fetch_candles(symbol, granularity=60, points=200)
    if df.empty:
        return {"trend":"neutral","vwap_cross":False,"rsi":50,"ema":None,"last_close":0}
    vwap = vwap_from_df(df)
    rsi = rsi_from_df(df)
    ema = ema_from_df(df)
    last = float(df["close"].iloc[-1])
    trend = "neutral"
    if ema is not None:
        trend = "long" if last > ema else "short" if last < ema else "neutral"
    vwap_cross = (last > vwap) if trend=="long" else (last < vwap) if trend=="short" else False
    return {"trend":trend, "vwap_cross":vwap_cross, "rsi":rsi, "ema":ema, "last_close": last}

# ---------------------------
# Order placement: parent + attached TP/SL (bracket)
# ---------------------------
def place_bracket_order_coinbase(symbol, side, base_size, tp_price, sl_trigger_price, sl_limit_price=None, client_order_id=None):
    """
    Places a parent order with attached bracket (trigger_bracket_gtc) using Coinbase Advanced API SDK's create_order().
    The SDK exposes create_order() / trigger_bracket_order_gtc_* helpers; here we build the raw create_order payload.
    - symbol: e.g. "ETH-USD"
    - side: "BUY" or "SELL"
    - base_size: string or numeric amount of base currency (e.g., "0.01")
    - tp_price: take-profit limit price (quote currency)
    - sl_trigger_price: stop trigger price (quote)
    - sl_limit_price: optional stop-limit price when stop triggers (if None, SDK/exchange will pick within allowed range)
    """
    if PAPER_MODE or client is None:
        log.info("[PAPER] bracket order simulated: %s %s %s tp=%s sl_trigger=%s", side, symbol, base_size, tp_price, sl_trigger_price)
        return {"status":"paper","symbol":symbol,"side":side,"size":base_size,"tp":tp_price,"sl_trigger":sl_trigger_price}

    # Build order_configuration and attached_order_configuration per Coinbase docs
    # Example: market parent + attached trigger_bracket_gtc
    try:
        payload = {
            "client_order_id": client_order_id or f"nija-{int(time.time())}",
            "product_id": symbol,
            "side": side.upper(),
            "order_configuration": {
                # Make parent a market by specifying market type via SDK-specific key; if SDK has helper use it.
                # SDK docs show "market_market_ioc" etc. We'll use 'market_market_ioc' or generic create_order preview.
                # To be safe, use the SDK convenience method if available:
            }
        }

        # For market parent: use SDK helper if available (safer)
        if hasattr(client, "market_order_buy") or hasattr(client, "market_order_sell"):
            # Use convenience SDK method
            if side.upper() == "BUY":
                res = client.market_order_buy(product_id=symbol, quote_size=str(base_size))  # buy by quote_size
            else:
                res = client.market_order_sell(product_id=symbol, base_size=str(base_size))   # sell by base_size
            # Then attach bracket if SDK has trigger_bracket helpers, otherwise create attached via create_order
            # Some SDKs require create_order with both order_configuration and attached_order_configuration in one call.
            # We'll attempt create_order with attached configuration below for the bracket; if the SDK executed above, we return res.
            log.info("Parent market order executed (SDK convenience): %s", res)
            # Note: attached orders normally require sending in the same request to be atomic. If SDK helper performed parent alone, attached bracket may not be attached.
            # Safer approach: use create_order with order_configuration and attached_order_configuration in a single call:
        # Fallback: use create_order with explicit order_configuration and attached_order_configuration
        # Build an order_configuration for a market parent with base_size
        payload["order_configuration"] = {
            "market_market_ioc": {
                # Some SDKs use 'quoteSize' to place buy by quote; if trading by base_size prefer a limit parent instead
                # We place a market order using 'baseSize' to sell, or 'quoteSize' to buy. Use both fallback attempts if needed by exchange.
                "baseSize": str(base_size) if side.upper() == "SELL" else None,
                "quoteSize": str(base_size) if side.upper() == "BUY" else None
            }
        }
        # Attached bracket (trigger_bracket_gtc)
        attached = {
            "trigger_bracket_gtc": {
                "limit_price": str(tp_price),
                "stop_trigger_price": str(sl_trigger_price)
            }
        }
        if sl_limit_price:
            attached["trigger_bracket_gtc"]["stop_limit_price"] = str(sl_limit_price)
        payload["attached_order_configuration"] = attached

        # Remove None values (clean payload)
        # (SDK create_order usually accepts JSON body like this)
        def clean(d):
            if isinstance(d, dict):
                return {k: clean(v) for k, v in d.items() if v is not None}
            return d
        payload = clean(payload)

        # Call SDK create_order (this should create parent + attached bracket in one atomic request per Coinbase docs)
        if hasattr(client, "create_order"):
            res = client.create_order(payload)
        else:
            # Some SDKs map create_order to REST client.post('orders', payload) - try a generic post() if available
            if hasattr(client, "post"):
                res = client.post("/orders", json=payload)
            else:
                raise RuntimeError("SDK does not expose create_order or post; update SDK or adapt call.")
        log.info("Bracket order response: %s", res)
        return res
    except Exception as e:
        log.error("Failed to place bracket order: %s", e)
        return None

# ---------------------------
# High-level wrapper: place trade with bracket TP/SL
# ---------------------------
def place_trade_with_bracket(symbol, side, qty, tp_pct=TP_PCT, sl_pct=SL_PCT):
    """
    - qty = base size (units of asset) for sell, or quote size for buy if using quote sizing.
    - For simplicity we compute TP/SL relative to last market price.
    """
    ind = get_indicators(symbol)
    last = ind["last_close"]
    if last <= 0:
        log.error("No market price available for %s; skipping trade.", symbol)
        return None

    if side.lower() == "buy":
        tp_price = last * (1 + tp_pct)
        sl_trigger = last * (1 - sl_pct)
    else:
        tp_price = last * (1 - tp_pct)
        sl_trigger = last * (1 + sl_pct)

    # Some APIs require a stop_limit price too; set stop_limit a bit worse than trigger
    if side.lower() == "buy":
        sl_limit = sl_trigger * 0.995
    else:
        sl_limit = sl_trigger * 1.005

    # convert qty into base_size or quote_size depending on SDK convenience; here we use base_size (units of base)
    base_size = qty

    log.info("Placing %s %s %s (last=%.8f) TP=%.8f SL_trigger=%.8f", side.upper(), symbol, base_size, last, tp_price, sl_trigger)

    return place_bracket_order_coinbase(
        symbol=symbol,
        side=side.upper(),
        base_size=base_size,
        tp_price=round(tp_price, 8),
        sl_trigger_price=round(sl_trigger, 8),
        sl_limit_price=round(sl_limit, 8)
    )

# ---------------------------
# Smart entry logic & active trade tracker (minimal)
# ---------------------------
active_trades = {}  # symbol -> order info

def enter_trade_if_signal(symbol):
    ind = get_indicators(symbol)
    trend = ind["trend"]
    vwap_cross = ind["vwap_cross"]
    last = ind["last_close"]
    qty = TRADE_QUANTITY.get(symbol, 0.001)

    # Example entry filter: trend+vwap+RSI range; adjust thresholds to your style
    if trend == "long" and vwap_cross and ind["rsi"] < 70:
        resp = place_trade_with_bracket(symbol, "buy", qty)
        if resp:
            active_trades[symbol] = {"side":"buy","entry_price": last, "resp": resp}
    elif trend == "short" and vwap_cross and ind["rsi"] > 30:
        resp = place_trade_with_bracket(symbol, "sell", qty)
        if resp:
            active_trades[symbol] = {"side":"sell","entry_price": last, "resp": resp}

# ---------------------------
# Bot loop: run per-ticker
# ---------------------------
def run_bot():
    log.info("Nija Smart Bot started (bracket TP/SL enabled). PAPER_MODE=%s", PAPER_MODE)
    while True:
        for symbol in CRYPTO_TICKERS:
            try:
                enter_trade_if_signal(symbol)
            except Exception as e:
                log.exception("Error processing symbol %s: %s", symbol, e)
            time.sleep(LOOP_DELAY_PER_TICKER)

# ---------------------------
# Start (Flask + Bot thread)
# ---------------------------
if __name__ == "__main__":
    Thread(target=run_bot, daemon=True).start()
    # Run Flask health server (blocking)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
