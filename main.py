# ===============================
# MAIN.PY FOR NIJA TRADING BOT
# ===============================

import os
import time
import logging
import requests
import importlib
from flask import Flask

# ---------------------------
# LOGGING
# ---------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("nija")

# ---------------------------
# PAPER MODE / ENV VARS
# ---------------------------
PAPER_MODE = os.getenv("PAPER_MODE", "0") == "1"
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")
TRADEVIEW_WEBHOOK_URL = os.getenv("TRADEVIEW_WEBHOOK_URL", "").strip()
CRYPTO_TICKERS = ["BTC-USD", "ETH-USD"]  # add more as needed

# ---------------------------
# ROBUST COINBASE CLIENT IMPORT
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
                    log.error("Coinbase API key/secret missing in env vars; switching to PAPER_MODE.")
                    PAPER_MODE = True
                else:
                    try:
                        client = ClientClass(api_key=COINBASE_API_KEY, api_secret=COINBASE_API_SECRET)
                        log.info("Imported Coinbase client from '%s' and initialized.", modname)
                    except Exception as e:
                        log.error("Imported %s but failed to initialize Client: %s", modname, e)
                        client = None
                        PAPER_MODE = True
                break
        except Exception as e:
            log.debug("Import candidate '%s' failed: %s", modname, e)
    else:
        log.error("No Coinbase client module found among candidates. Switching to PAPER_MODE.")
        PAPER_MODE = True
else:
    log.info("PAPER_MODE enabled via environment variable.")

# ---------------------------
# FLASK APP
# ---------------------------
app = Flask(__name__)

@app.route("/")
def health():
    return "Nija Trading Bot Live ✅", 200

# ---------------------------
# PLACE ORDER SAFELY
# ---------------------------
def place_order_safe(symbol: str, side: str, qty: float):
    """
    Safely place an order:
    - PAPER_MODE: returns simulated order
    - LIVE_MODE: uses Coinbase client
    """
    if PAPER_MODE:
        fake_id = f"paper-{int(time.time())}"
        log.info(f"[PAPER] Simulated {side.upper()} {symbol} x{qty} (id={fake_id})")
        return {"success": True, "result": {"id": fake_id, "size": qty}}

    if client is None:
        err = "Coinbase client not initialized"
        log.error(err)
        return {"success": False, "error": err}

    try:
        res = client.place_order(
            product_id=symbol,
            side=side.lower(),   # must be "buy" or "sell"
            type="market",
            size=str(qty)
        )
        log.info("Placed LIVE order: %s %s x%s -> %s", side.upper(), symbol, qty, res)
        return {"success": True, "result": res}
    except Exception as e:
        log.error("Live order failed for %s %s x%s: %s", side, symbol, qty, e)
        return {"success": False, "error": str(e)}

# ---------------------------
# GET LIVE BALANCES
# ---------------------------
def get_balance_safe():
    """
    Fetch live balances from Coinbase client.
    """
    if PAPER_MODE:
        log.warning("get_balance_safe called in PAPER_MODE — returning simulated balances.")
        return {"success": True, "balances": {"USD": 100.0}}

    if client is None:
        err = "Coinbase client not initialized"
        log.error(err)
        return {"success": False, "error": err}

    try:
        accounts = client.get_accounts()
        balances = {}
        rows = getattr(accounts, "data", accounts)  # supports dict or object
        for a in rows:
            currency = a.get("currency") or getattr(a, "currency", None)
            available = None
            if isinstance(a.get("available"), dict):
                available = float(a["available"].get("value", 0.0))
            elif a.get("available") is not None:
                available = float(a["available"])
            if currency and available is not None:
                balances[currency] = available
        log.info("Fetched balances: %s", balances)
        return {"success": True, "balances": balances}
    except Exception as e:
        log.error("Failed to fetch balances: %s", e)
        return {"success": False, "error": str(e)}

# ---------------------------
# SEND BALANCES TO TRADINGVIEW
# ---------------------------
def send_tradeview_balance(balances: dict):
    if not TRADEVIEW_WEBHOOK_URL:
        log.debug("TRADEVIEW_WEBHOOK_URL not set — skipping balance sync.")
        return {"success": False, "error": "no-webhook-url"}

    try:
        payload = {"balances": balances, "ts": int(time.time())}
        resp = requests.post(TRADEVIEW_WEBHOOK_URL, json=payload, timeout=6)
        if 200 <= resp.status_code < 300:
            log.info("Sent balances to TradingView webhook: %s", payload)
            return {"success": True, "status_code": resp.status_code}
        else:
            log.warning("TradingView webhook returned %s: %s", resp.status_code, resp.text)
            return {"success": False, "status_code": resp.status_code, "body": resp.text}
    except Exception as e:
        log.error("Failed to send balance to TradingView: %s", e)
        return {"success": False, "error": str(e)}

# ---------------------------
# MAIN BOT LOOP
# ---------------------------
def run_bot():
    while True:
        for symbol in CRYPTO_TICKERS:
            # Example: buy tiny amount
            place_order_safe(symbol, side="buy", qty=0.001)
            time.sleep(10)  # adjust timing

# ---------------------------
# ENTRY POINT
# ---------------------------
if __name__ == "__main__":
    from threading import Thread
    Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
