import os
import time
import logging
from datetime import datetime
from flask import Flask, request, jsonify

# ----------------------
# Logging
# ----------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("nija_bot")

# ----------------------
# Flask App
# ----------------------
app = Flask(__name__)

# ----------------------
# Trading Control
# ----------------------
TRADING_ENABLED = os.getenv("TRADING_ENABLED", "false").lower() == "true"
ENV = os.getenv("ENV", "production")  # optional

trade_count = 0
trade_history = []  # store trades

def record_trade(trade_record: dict):
    global trade_count, trade_history
    trade_count += 1
    trade_record["id"] = trade_count
    trade_record["timestamp_iso"] = datetime.utcnow().isoformat() + "Z"
    trade_history.append(trade_record)
    log.info("Recorded trade: %s", trade_record)

# ----------------------
# Status endpoint
# ----------------------
@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "ok": True,
        "env": ENV,
        "trading_enabled": TRADING_ENABLED,
        "trade_count": trade_count,
        "last_trade": trade_history[-1] if trade_history else None
    }), 200

# ----------------------
# Trades endpoint
# ----------------------
@app.route("/trades", methods=["GET"])
def trades():
    return jsonify({"total_trades": trade_count, "history": trade_history[-100:]}), 200

# ----------------------
# Order placement wrapper
# ----------------------
def place_order_wrapper(side: str, size: float, price: float = None, product_id: str = "BTC-USD", max_retries=3):
    global TRADING_ENABLED
    note = ""

    if not TRADING_ENABLED:
        note = "TRADING_DISABLED - simulated order recorded"
        log.warning("Trading disabled. Simulating %s %s @ %s", side, size, price)
        trade = {"side": side, "size": size, "price": price, "status": "simulated", "note": note}
        record_trade(trade)
        return trade

    COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
    COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")
    COINBASE_API_PASSPHRASE = os.getenv("COINBASE_API_PASSPHRASE")

    if not COINBASE_API_KEY or not COINBASE_API_SECRET:
        note = "MISSING_API_KEYS"
        log.error("Missing API keys. Aborting order.")
        trade = {"side": side, "size": size, "price": price, "status": "failed", "note": note}
        record_trade(trade)
        return trade

    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            log.info("Placing order attempt %d/%d: %s %s @ %s on %s", attempt, max_retries, side, size, price, product_id)

            # ---- Simulated / placeholder order ----
            # Replace this block with your actual API client call
            result = {
                "order_id": f"sim-{int(time.time())}",
                "side": side,
                "size": size,
                "price": price,
                "status": "filled",
                "filled_qty": size,
            }

            trade = {
                "order_id": result.get("order_id"),
                "side": side,
                "size": size,
                "price": result.get("price", price),
                "status": result.get("status", "unknown"),
                "raw": result,
                "note": f"placed via attempt {attempt}"
            }
            record_trade(trade)
            return trade

        except Exception as e:
            last_err = str(e)
            log.exception("Order attempt %d failed: %s", attempt, e)
            time.sleep(1 * attempt)

    trade = {"side": side, "size": size, "price": price, "status": "failed", "note": f"all attempts failed: {last_err}"}
    record_trade(trade)
    return trade

# ----------------------
# Test-order route
# ----------------------
@app.route("/test-order", methods=["POST"])
def test_order():
    data = request.json or {}
    side = data.get("side", "buy")
    size = float(data.get("size", 0.001))
    price = data.get("price", None)
    result = place_order_wrapper(side=side, size=size, price=price)
    return jsonify(result), 200

# ----------------------
# Run app
# ----------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    log.info("Starting Nija Trading Bot Flask app on port %s (TRADING_ENABLED=%s)", port, TRADING_ENABLED)
    app.run(host="0.0.0.0", port=port)
