# nija_bot.py
# Minimal safe Flask app for Nija trading bot.
# IMPORTANT: This file will NOT place live trades unless ENABLE_TRADING=True and USE_MOCK=False

from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import logging
import traceback

load_dotenv()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("nija_bot")

app = Flask(__name__)

# Safety flags (default to safe)
USE_MOCK = os.getenv("USE_MOCK", "True").lower() in ("1", "true", "yes")
ENABLE_TRADING = os.getenv("ENABLE_TRADING", "False").lower() in ("1", "true", "yes")
CONFIRM_BEFORE_TRADE = os.getenv("CONFIRM_BEFORE_TRADE", "True").lower() in ("1", "true", "yes")

# Coinbase credentials loaded from environment (do NOT commit .env with real keys)
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
API_PEM_B64 = os.getenv("API_PEM_B64")

# Try import coinbase_advanced_py but keep app running if missing
COINBASE_AVAILABLE = False
COINBASE_IMPORT_ERROR = None
try:
    import coinbase_advanced_py as cb
    COINBASE_AVAILABLE = True
except Exception as e:
    COINBASE_AVAILABLE = False
    COINBASE_IMPORT_ERROR = traceback.format_exc()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "use_mock": USE_MOCK,
        "enable_trading": ENABLE_TRADING,
        "confirm_before_trade": CONFIRM_BEFORE_TRADE
    })

@app.route("/check-coinbase", methods=["GET"])
def check_coinbase():
    # returns whether the coinbase module can be imported inside the running environment
    return jsonify({
        "coinbase_available": COINBASE_AVAILABLE,
        "import_error": None if COINBASE_AVAILABLE else COINBASE_IMPORT_ERROR
    })

def _safe_place_order(symbol, size, side, price=None):
    """
    This function will only perform a real order if:
      - ENABLE_TRADING is True
      - USE_MOCK is False
    Otherwise it will simulate and return a simulated order response.
    IMPORTANT: Replace the placeholder below with the actual coinbase-advanced-py order call
               only after confirming the library API and testing on testnet / sandbox.
    """
    log.info(f"Order request -> symbol:{symbol} size:{size} side:{side} price:{price}")
    if USE_MOCK:
        log.info("USE_MOCK is True -> returning simulated order (no real trade).")
        return {"status": "simulated", "symbol": symbol, "size": size, "side": side, "price": price}

    if not ENABLE_TRADING:
        log.warning("ENABLE_TRADING is False -> refusing to place a live order.")
        return {"status": "refused", "reason": "ENABLE_TRADING is False"}

    if not COINBASE_AVAILABLE:
        log.error("Coinbase client not available in environment.")
        return {"status": "error", "reason": "coinbase client missing"}

    # --- PLACEHOLDER: actual Coinbase order logic goes here ---
    # Read the coinbase-advanced-py docs and implement the real call.
    # Example (pseudocode, DO NOT paste blindly):
    #
    # client = cb.Client(api_key=API_KEY, api_secret=API_SECRET, pem_b64=API_PEM_B64)
    # order = client.create_order(product_id=symbol, side=side, size=size, price=price, type="limit")
    # return {"status":"placed", "order": order}
    #
    # Replace this simulated response with the real order above *after* you verify in a sandbox.
    log.info("WARNING: This is a placeholder. Implement the real coinbase order here AFTER verifying.")
    return {"status": "placeholder", "message": "Replace placeholder with real coinbase order call after verification."}

@app.route("/simulate-order", methods=["POST"])
def simulate_order():
    body = request.get_json(force=True, silent=True) or {}
    symbol = body.get("symbol", "BTC-USD")
    size = body.get("size", "0.001")
    side = body.get("side", "buy")
    price = body.get("price")
    resp = _safe_place_order(symbol, size, side, price)
    return jsonify({"result": resp})

@app.route("/trade", methods=["POST"])
def trade():
    """
    Place a live trade only when ENABLE_TRADING=True and USE_MOCK=False.
    This endpoint still requires you to flip the environment flags in Render or in your .env.
    """
    body = request.get_json(force=True, silent=True) or {}
    symbol = body.get("symbol")
    size = body.get("size")
    side = body.get("side")
    price = body.get("price")

    # Basic validation
    if not (symbol and size and side):
        return jsonify({"status": "error", "reason": "missing symbol/size/side"}), 400

    # Confirm safety
    if CONFIRM_BEFORE_TRADE:
        # Log and refuse — this forces you to explicitly turn off the confirm flag
        log.info("CONFIRM_BEFORE_TRADE=True -> require manual confirmation. Refusing to trade.")
        return jsonify({"status": "refused", "reason": "CONFIRM_BEFORE_TRADE is True. Set to False to proceed."}), 403

    # Place the order (or simulated depending on flags)
    result = _safe_place_order(symbol, size, side, price)
    return jsonify({"result": result})

if __name__ == "__main__":
    # For local dev only. Render will use gunicorn to run app.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
