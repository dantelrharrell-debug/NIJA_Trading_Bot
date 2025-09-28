# nija.py (patched full version)

from flask import Flask, request, jsonify
from decimal import Decimal, InvalidOperation
import os, re, traceback
from dotenv import load_dotenv
import ccxt

# ------------------------------
# CONFIG
# ------------------------------
load_dotenv()  # load .env in current folder

COINBASE_SPOT_KEY = os.getenv("COINBASE_SPOT_KEY")
COINBASE_SPOT_SECRET = os.getenv("COINBASE_SPOT_SECRET")

DRY_RUN = True  # True = simulate orders, False = live trading

# ------------------------------
# INIT BOT & CLIENT
# ------------------------------
app = Flask(__name__)

spot = None
if COINBASE_SPOT_KEY and COINBASE_SPOT_SECRET and not DRY_RUN:
    try:
        spot = ccxt.coinbasepro({
            "apiKey": COINBASE_SPOT_KEY,
            "secret": COINBASE_SPOT_SECRET,
        })
        print("✅ Spot client initialized.")
    except Exception as e:
        print("❌ Failed to init spot client:", repr(e))
else:
    if not COINBASE_SPOT_KEY or not COINBASE_SPOT_SECRET:
        print("⚠️ Missing spot API keys in .env")
    if DRY_RUN:
        print("🟡 DRY_RUN enabled — orders will be simulated.")

# ------------------------------
# HELPER: Mask sensitive data in webhook payload
# ------------------------------
KEY_RE = re.compile(r'^[A-Za-z0-9\-_]{20,}$')  # likely API keys / secrets

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

# ------------------------------
# WEBHOOK HANDLER
# ------------------------------
@app.route("/webhook", methods=["POST"])
def webhook_post():
    try:
        raw = request.get_json(force=True, silent=True)
        masked = mask_payload(raw) if raw else None
        print("📩 Signal Received (masked):", masked)

        if not raw:
            return jsonify({"status":"error","message":"invalid json or empty body"}), 400

        symbol = raw.get("symbol", "BTC-USD")
        side = raw.get("side", "buy")
        amount_raw = raw.get("amount", None)

        if amount_raw is None:
            return jsonify({"status":"error","message":"missing amount"}), 400

        # SAFE parse decimal
        try:
            if isinstance(amount_raw, (int, float, Decimal)):
                amount = Decimal(str(amount_raw))
            else:
                amount = Decimal(str(amount_raw).strip())
            if amount <= 0:
                return jsonify({"status":"error","message":"amount must be > 0"}), 400
        except (InvalidOperation, ValueError):
            print("❌ Invalid amount value received:", amount_raw)
            return jsonify({"status":"error","message":"invalid amount, must be numeric"}), 400

        # normalize symbol for Coinbase
        if "/" in symbol:
            symbol = symbol.replace("/", "-")

        print(f"Parsed order -> symbol={symbol} side={side} amount={amount} DRY_RUN={DRY_RUN}")

        if DRY_RUN:
            simulated = {"symbol": symbol, "side": side, "amount": str(amount), "note": "dry-run (no real order)"}
            print("🟡 DRY_RUN true — simulated order:", simulated)
            return jsonify({"status":"dry-run","result": simulated}), 200

        # LIVE order
        if not spot:
            print("❌ Spot client not configured (missing keys).")
            return jsonify({"status":"error","message":"spot client not configured"}), 500

        try:
            full_order = spot.create_market_order(symbol, side, float(amount))
            print("✅ Full order result (CCXT):", full_order)
            return jsonify({"status":"success","order": full_order}), 200
        except Exception as order_exc:
            print("❌ Exception placing order:", repr(order_exc))
            traceback.print_exc()
            return jsonify({"status":"error","message": str(order_exc)}), 500

    except Exception as e:
        print("❌ Unexpected exception in webhook_post:", repr(e))
        traceback.print_exc()
        return jsonify({"status":"error","message":"internal server error"}), 500

# ------------------------------
# HEARTBEAT
# ------------------------------
@app.before_first_request
def startup_heartbeat():
    print("✅ NijaBot initialized")
    print("🔄 NijaBot heartbeat: waiting for webhook trades...")
    print("🚀 Nija Trading Bot live. Listening for webhooks at /webhook")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
