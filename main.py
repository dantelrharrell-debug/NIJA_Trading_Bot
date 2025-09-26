# main.py -- Replit-ready Nija perp test-run wired to your signal function if you provide it.
# Put your signal function in signals.py as:
# def get_nija_signals() -> dict:
#     return {"BTC":"long","ETH":"short", ...}
#
# Defaults: SAFE TEST MODE (doesn't run live Coinbase unless you set RUN_LIVE=yes + secrets).
# To run live set RUN_LIVE=yes and add COINBASE_API_KEY / COINBASE_API_SECRET as Replit secrets.

import os
import time
import math
import logging
from typing import Optional, Dict

# ----- CONFIG -----
BASE_COINS = ["BTC", "ETH", "SOL", "XRP", "ADA", "LTC"]
ORDER_USD = 1.0
STOP_DISTANCE_PCT = 0.02
ORDER_CADENCE_SEC = 1.0
# ------------------

RUN_LIVE = os.getenv("RUN_LIVE", "").lower() == "yes"
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY", None)
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET", None)
COINBASE_API_PASSPHRASE = os.getenv("COINBASE_API_PASSPHRASE", None)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("nija_replit_wired")

try:
    import ccxt
except Exception:
    logger.error("ccxt not installed. Add ccxt to packages or run: pip install ccxt")
    raise

# --- Try to import user's signal function from signals.py ---
def load_user_signals_func():
    """
    Looks for signals.py with function get_nija_signals() that returns a dict:
      {"BTC":"long","ETH":"short",...}
    If not found, returns None.
    """
    try:
        import signals  # user should create signals.py in Replit
        if hasattr(signals, "get_nija_signals"):
            logger.info("Found user signals.get_nija_signals() — will use it.")
            return signals.get_nija_signals
        else:
            logger.warning("signals.py found but no get_nija_signals() function inside.")
    except Exception as e:
        logger.info("No user signals.py found or import error (that's fine). Using demo signals.")
    return None

# --- Exchange creation helpers (same safe/testnet logic as before) ---
def create_test_exchange() -> ccxt.Exchange:
    try:
        ex = ccxt.bybit({
            "apiKey": "",
            "secret": "",
            "enableRateLimit": True,
            "options": {"defaultType": "swap"},
        })
        if hasattr(ex, "set_sandbox_mode"):
            ex.set_sandbox_mode(True)
            logger.info("Using Bybit sandbox for test trades.")
        ex.load_markets(True)
        return ex
    except Exception as e:
        logger.warning("Bybit not available: %s", e)
    try:
        ex = ccxt.binance({
            "apiKey": "",
            "secret": "",
            "enableRateLimit": True,
            "options": {"defaultType": "future"},
        })
        if hasattr(ex, "set_sandbox_mode"):
            ex.set_sandbox_mode(True)
            logger.info("Using Binance sandbox for test trades.")
        ex.load_markets(True)
        return ex
    except Exception as e:
        logger.warning("Binance sandbox not available: %s", e)
    try:
        ex = ccxt.coinbase({
            "enableRateLimit": True,
            "options": {"defaultType": "perpetual"},
        })
        ex.load_markets(True)
        logger.info("Fallback: using coinbase markets (may be read-only).")
        return ex
    except Exception as e:
        logger.error("No usable test exchange available: %s", e)
        raise

def create_coinbase_exchange_live(api_key: str, api_secret: str, passphrase: Optional[str] = None) -> ccxt.Exchange:
    kwargs = {
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
        "options": {"defaultType": "perpetual"},
    }
    if passphrase:
        kwargs["password"] = passphrase
    # Some CCXT versions have coinbasepro, else coinbase
    ex = ccxt.coinbasepro(kwargs) if hasattr(ccxt, "coinbasepro") else ccxt.coinbase(kwargs)
    ex.load_markets(True)
    logger.info("Initialized live Coinbase (CCXT).")
    return ex

# --- Market helpers ---
def find_perp_market(exchange: ccxt.Exchange, base: str) -> Optional[str]:
    base_up = base.upper()
    for symbol, m in exchange.markets.items():
        try:
            if m.get("base","").upper() != base_up:
                continue
            mtype = m.get("type","") or str(m.get("info",""))
            if any(k in str(mtype).lower() for k in ("swap","perpetual","future")):
                return symbol
            if "PERP" in symbol.upper() or "SWAP" in symbol.upper():
                return symbol
        except Exception:
            continue
    for symbol, m in exchange.markets.items():
        if m.get("base","").upper() == base_up:
            return symbol
    return None

def tiny_order_qty_from_usd(exchange: ccxt.Exchange, market_symbol: str, usd_amount: float) -> float:
    ticker = exchange.fetch_ticker(market_symbol)
    price = float(ticker["last"])
    qty = usd_amount / price if price > 0 else 0.0
    try:
        prec = exchange.markets[market_symbol].get("precision", {}).get("amount")
        if prec and prec < 1:
            places = int(round(-math.log10(prec)))
            return float(round(qty, places))
    except Exception:
        pass
    return float(qty)

def place_market_order(exchange: ccxt.Exchange, symbol: str, side: str, qty: float, params: Optional[dict]=None):
    params = params or {}
    try:
        logger.info("Placing market order: %s %s %s", side, qty, symbol)
        order = exchange.create_order(symbol, "market", side, qty, None, params)
        logger.info("Order result: %s", order)
        return order
    except Exception as e:
        logger.error("Market order failed for %s: %s", symbol, e)
        return None

# --- Core test cycle wired to signals ---
def run_test_cycle(exchange: ccxt.Exchange, get_signals_fn):
    exchange.load_markets(True)
    # Map bases to markets
    market_map = {}
    for base in BASE_COINS:
        market = find_perp_market(exchange, base)
        market_map[base] = market
    logger.info("Market mapping:")
    for b, m in market_map.items():
        logger.info("  %s -> %s", b, m or "(no market found)")

    # Fetch signals (either user function or demo)
    try:
        signals = get_signals_fn()
        if not isinstance(signals, dict):
            raise ValueError("get_nija_signals must return a dict. Using demo signals instead.")
        logger.info("Using user signals: %s", signals)
    except Exception as e:
        logger.warning("User signals failed or not found (%s). Using demo signals.", e)
        # demo: alternating long/short to show both flows
        signals = {}
        t = int(time.time())
        for i, b in enumerate(BASE_COINS):
            signals[b] = "long" if (t//30 + i) % 2 == 0 else "short"
        logger.info("Demo signals: %s", signals)

    # Execute tiny test trades per signals
    for base, signal in signals.items():
        market = market_map.get(base)
        if not market:
            logger.warning("Skipping %s: no market found.", base)
            continue
        try:
            qty = tiny_order_qty_from_usd(exchange, market, ORDER_USD)
            if qty <= 0:
                logger.warning("Qty <= 0 for %s; skipping", market)
                continue
            if signal == "long":
                side = "buy"
            elif signal == "short":
                side = "sell"
            else:
                logger.info("Signal for %s is flat. Skipping.", base)
                continue

            if RUN_LIVE:
                logger.info("LIVE MODE: placing %s %s %s", side, qty, market)
                place_market_order(exchange, market, side, qty)
                time.sleep(0.3)
                # close immediately by reversing
                place_market_order(exchange, market, "sell" if side=="buy" else "buy", qty)
            else:
                logger.info("TEST MODE: attempting sandbox %s %s %s", side, qty, market)
                try:
                    place_market_order(exchange, market, side, qty)
                    time.sleep(0.3)
                    place_market_order(exchange, market, "sell" if side=="buy" else "buy", qty)
                except Exception as e:
                    logger.warning("Sandbox orders may not be supported for %s: %s", market, e)

            time.sleep(ORDER_CADENCE_SEC)
        except Exception as e:
            logger.exception("Error handling %s (%s): %s", base, market, e)

def main():
    logger.info("Nija wired test-run starting. RUN_LIVE=%s", RUN_LIVE)
    # prepare signals function
    user_fn = load_user_signals_func()
    if user_fn:
        get_signals_fn = user_fn
    else:
        # fallback demo provider
        def demo_signals():
            t = int(time.time())
            out = {}
            for i, b in enumerate(BASE_COINS):
                out[b] = "long" if (t//30 + i) % 2 == 0 else "short"
            return out
        get_signals_fn = demo_signals

    if RUN_LIVE:
        if not COINBASE_API_KEY or not COINBASE_API_SECRET:
            logger.error("RUN_LIVE requested but Coinbase keys not set. Aborting.")
            return
        try:
            exchange = create_coinbase_exchange_live(COINBASE_API_KEY, COINBASE_API_SECRET, COINBASE_API_PASSPHRASE)
            run_test_cycle(exchange, get_signals_fn)
        except Exception as e:
            logger.exception("Live run failed: %s", e)
    else:
        try:
            exchange = create_test_exchange()
            run_test_cycle(exchange, get_signals_fn)
        except Exception as e:
            logger.exception("Test run failed: %s", e)

if __name__ == "__main__":
    main()
