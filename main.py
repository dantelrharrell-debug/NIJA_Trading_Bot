# main.py -- Nija Futures Bot (sandbox -> live)
import os
import time
import math
import logging

BASE_COINS = ["BTC","ETH","SOL","XRP","ADA","LTC"]
ORDER_USD = 1.0
ORDER_CADENCE_SEC = 1.0

RUN_LIVE = os.getenv("RUN_LIVE", "").lower() == "yes"
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY", None)
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET", None)
COINBASE_API_PASSPHRASE = os.getenv("COINBASE_API_PASSPHRASE", None)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("nija_futures_bot")

try:
    import ccxt
except Exception:
    logger.error("ccxt not installed. Add to requirements.txt")
    raise

# Load your signals
def load_signals():
    try:
        import signals
        return signals.get_nija_signals
    except Exception:
        logger.warning("signals.py missing, using demo signals")
        return lambda: {b: "long" for b in BASE_COINS}

# Tiny order qty
def tiny_qty(exchange, market, usd_amount):
    ticker = exchange.fetch_ticker(market)
    price = float(ticker["last"])
    qty = usd_amount / price if price > 0 else 0
    try:
        prec = exchange.markets[market].get("precision", {}).get("amount")
        if prec and prec < 1:
            qty = round(qty, int(round(-math.log10(prec))))
    except: pass
    return float(qty)

# Place order
def place_order(exchange, symbol, side, qty):
    try:
        logger.info(f"Placing {side} order: {qty} {symbol}")
        order = exchange.create_order(symbol, "market", side, qty)
        logger.info(f"Order result: {order}")
        return order
    except Exception as e:
        logger.error(f"Failed {symbol}: {e}")
        return None

# Find perp/futures market
def find_market(exchange, base):
    for symbol, m in exchange.markets.items():
        if m.get("base","").upper()==base.upper() and ("swap" in str(m.get("type","")).lower() or "perpetual" in str(m.get("type","")).lower() or "future" in str(m.get("type","")).lower()):
            return symbol
    return None

# Sandbox exchange
def create_sandbox():
    for ex_name in ["bybit","binance","coinbase"]:
        try:
            ex_cls = getattr(ccxt, ex_name)
            ex = ex_cls({"enableRateLimit": True})
            if hasattr(ex, "set_sandbox_mode"):
                ex.set_sandbox_mode(True)
                logger.info(f"{ex_name} sandbox ready")
            ex.load_markets(True)
            return ex
        except: continue
    raise RuntimeError("No sandbox available")

# Live Coinbase
def create_live():
    if not COINBASE_API_KEY or not COINBASE_API_SECRET:
        raise RuntimeError("Live requested but Coinbase keys missing")
    ex = ccxt.coinbasepro({
        "apiKey": COINBASE_API_KEY,
        "secret": COINBASE_API_SECRET,
        "password": COINBASE_API_PASSPHRASE,
        "enableRateLimit": True
    }) if hasattr(ccxt, "coinbasepro") else ccxt.coinbase({
        "apiKey": COINBASE_API_KEY,
        "secret": COINBASE_API_SECRET,
        "password": COINBASE_API_PASSPHRASE,
        "enableRateLimit": True
    })
    ex.load_markets(True)
    logger.info("Live Coinbase ready")
    return ex

# Run one cycle
def run_cycle(exchange):
    get_signals = load_signals()
    signals = get_signals()
    market_map = {b: find_market(exchange, b) for b in BASE_COINS}
    logger.info(f"Markets: {market_map}")

    for base, signal in signals.items():
        market = market_map.get(base)
        if not market: 
            logger.warning(f"No market for {base}")
            continue
        qty = tiny_qty(exchange, market, ORDER_USD)
        if qty <= 0: continue
        side = "buy" if signal=="long" else "sell" if signal=="short" else None
        if not side: continue
        place_order(exchange, market, side, qty)
        time.sleep(0.3)
        place_order(exchange, market, "sell" if side=="buy" else "buy", qty)
        time.sleep(ORDER_CADENCE_SEC)

# Main
def main():
    logger.info("Nija Futures Bot starting")
    if RUN_LIVE:
        logger.info("RUN_LIVE=yes detected")
        try:
            ex = create_live()
        except Exception as e:
            logger.error(f"Live setup failed: {e}, falling back to sandbox")
            ex = create_sandbox()
    else:
        ex = create_sandbox()
    run_cycle(ex)
    logger.info("Nija run finished")

if __name__ == "__main__":
    main()
