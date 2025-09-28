# main.py
from flask import Flask, request, jsonify
from decimal import Decimal, InvalidOperation
import re, traceback, os
import ccxt
from dotenv import load_dotenv

# ---------------------------
# Load environment variables
# ---------------------------
load_dotenv()
DRY_RUN = os.getenv("DRY_RUN", "True").lower() == "true"

COINBASE_SPOT_KEY = os.getenv("COINBASE_SPOT_KEY")
COINBASE_SPOT_SECRET = os.getenv("COINBASE_SPOT_SECRET")

# ---------------------------
# Flask app setup
# ---------------------------
app = Flask(__name__)

# ---------------------------
# Coinbase Spot client setup
# ---------------------------
spot = None
if not DRY_RUN:
    try:
        if not COINBASE_SPOT_KEY or not COINBASE_SPOT_SECRET:
            raise ValueError("Missing Coinbase Spot API keys")
        spot = ccxt.coinbasepro({
            "apiKey": COINBASE_SPOT_KEY,
            "secret": COINBASE_SPOT_SECRET,
        })
        print("✅ Spot client initialized")
    except Exception as e:
        print("⚠️ Spot client NOT initialized:", e)

# ---------------------------
# Helpers for masking keys
# ---------------------------
KEY_RE = re.compile(r'^[A-Za-z0-9\-_]{20,}$')

def mask_value(v):
    if not isinstance(v, str):
        return v
    v_str = v.strip()
    if KEY_RE.match(v_str):
        return v_str[:4] + "..." + v_str[-4:]
    return re.sub(r'([A-Za-z0-9\-_]{20,})', lambda m: m.group(0)[:4]+"..."+m.group(0)[-4:], v_str)

def mask_payload(obj):
    if isinstance(obj, dict): return {k: mask_payload(v) for k,v in obj.items()}
    if isinstance(obj, list): return [mask_payload(v) for v in obj]
    if isinstance(obj, str): return mask_value(obj)
    return obj

# ---------------------------
# Webhook handler
# ---------------------------
@app.route("/webhook", methods=["POST"])
def webhook_post():
    try:
        raw = request.get_json(force=True, silent=True)
        masked = mask_payload(raw) if raw else None
        print("📩 Signal Received (masked):", masked)

        if not raw:
            return jsonify({"status":"error","message":"invalid json"}), 400

        symbol = raw.get("symbol", "BTC-USD")
        side = raw.get("side", "buy")
        amount_raw = raw.get("amount")
        if amount_raw is None:
            return jsonify({"status":"error","message":"missing amount"}), 400

        # parse amount safely
        try:
            amount = Decimal(str(amount_raw).strip()) if not isinstance(amount_raw, (int,float,Decimal)) else Decimal(str(amount_raw))
            if amount <= 0:
                return jsonify({"status":"error","message":"amount must be >0"}), 400
        except (InvalidOperation, ValueError):
            return jsonify({"status":"error","message":"invalid amount"}), 400

        if "/" in symbol:
            symbol = symbol.replace("/", "-")

        print(f"Parsed order -> symbol={symbol} side={side} amount={amount} DRY_RUN={DRY_RUN}")

        # DRY_RUN: simulate
        if DRY_RUN:
            simulated = {"symbol": symbol, "side": side, "amount": str(amount), "note":"dry-run"}
            print("🟡 DRY_RUN simulated order:", simulated)
            return jsonify({"status":"dry-run","result": simulated}), 200

        # Live order
        if not spot:
            return jsonify({"status":"error","message":"spot client not configured"}), 500

        try:
            full_order = spot.create_market_order(symbol, side, float(amount))
            print("✅ Full order result:", full_order)
            return jsonify({"status":"success","order": full_order}), 200
        except Exception as e:
            print("❌ Exception placing order:", repr(e))
            traceback.print_exc()
            return jsonify({"status":"error","message": str(e)}), 500

    except Exception as e:
        print("❌ Unexpected exception:", repr(e))
        traceback.print_exc()
        return jsonify({"status":"error","message":"internal server error"}), 500

# ---------------------------
# Run app
# ---------------------------
if __name__ == "__main__":
    print("🚀 Nija Trading Bot live. DRY_RUN =", DRY_RUN)
    app.run(host="0.0.0.0", port=8080)
