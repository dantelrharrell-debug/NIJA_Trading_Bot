from decimal import Decimal, InvalidOperation
import re
import traceback
from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

# ----- Masking helpers -----
KEY_RE = re.compile(r'^[A-Za-z0-9\-_]{20,}$')

def mask_value(v):
    if not isinstance(v, str):
        return v
    v_str = v.strip()
    if KEY_RE.match(v_str):
        return v_str[:4] + "..." + v_str[-4:]
    return re.sub(r'([A-Za-z0-9\-_]{20,})', lambda m: m.group(0)[:4] + "..." + m.group(0)[-4:], v_str)

def mask_payload(obj):
    if isinstance(obj, dict):
        return {k: mask_payload(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [mask_payload(v) for v in obj]
    if isinstance(obj, str):
        return mask_value(obj)
    return obj

# ----- AI Top-Ticker Logic -----
def get_daily_top_ticker():
    """
    Replace this with your AI module that searches market data daily
    and picks the fastest, highest-profit ticker.
    For demo, we return BTC/USD.
    """
    # TODO: integrate your AI logic here
    return "BTC-USD"

# ----- Webhook Handler -----
@app.route("/webhook", methods=["POST"])
def webhook_post():
    try:
        raw = request.get_json(force=True, silent=True)
        masked = mask_payload(raw) if raw else None
        print("📩 Signal Received (masked):", masked)

        if not raw:
            return jsonify({"status":"error","message":"invalid json or empty body"}), 400

        # Get AI ticker automatically
        symbol = raw.get("symbol") or get_daily_top_ticker()
        side = raw.get("side", "buy")
        amount_raw = raw.get("amount")

        if amount_raw is None:
            return jsonify({"status":"error","message":"missing amount"}), 400

        # Safe Decimal parsing
        try:
            if isinstance(amount_raw, (int, float, Decimal)):
                amount = Decimal(str(amount_raw))
            else:
                amount = Decimal(str(amount_raw).strip())
            if amount <= 0:
                return jsonify({"status":"error","message":"amount must be > 0"}), 400
        except (InvalidOperation, ValueError) as e:
            print("❌ Invalid amount value received:", amount_raw)
            return jsonify({"status":"error","message":"invalid amount, must be numeric"}), 400

        # Normalize symbol
        if "/" in symbol:
            symbol = symbol.replace("/", "-")

        print(f"Parsed order -> symbol={symbol} side={side} amount={amount} DRY_RUN={DRY_RUN}")

        if DRY_RUN:
            simulated = {"symbol": symbol, "side": side, "amount": str(amount), "note": "dry-run"}
            print("🟡 DRY_RUN simulated order:", simulated)
            return jsonify({"status":"dry-run","result": simulated}), 200

        # Spot client must exist
        if not spot:
            print("❌ Spot client not configured")
            return jsonify({"status":"error","message":"spot client not configured"}), 500

        # Place market order
        try:
            full_order = spot.create_market_order(symbol, side, float(amount))
            print("✅ Full order result:", full_order)
            return jsonify({"status":"success","order": full_order}), 200
        except Exception as order_exc:
            print("❌ Exception placing order:", repr(order_exc))
            traceback.print_exc()
            return jsonify({"status":"error","message": str(order_exc)}), 500

    except Exception as e:
        print("❌ Unexpected exception:", repr(e))
        traceback.print_exc()
        return jsonify({"status":"error","message":"internal server error"}), 500

# ----- Heartbeat -----
@app.before_first_request
def start_heartbeat():
    print("🔄 NijaBot heartbeat started at", datetime.datetime.now())
