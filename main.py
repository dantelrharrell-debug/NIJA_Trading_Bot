from flask import Flask, request, jsonify
from decimal import Decimal, InvalidOperation
import json
import traceback
import re
import os
from datetime import datetime

# ==========================
# Config / Toggle
# ==========================
DRY_RUN = True  # Toggle to False for live trading
AI_MEMORY_FILE = "ai_memory.json"

# ==========================
# Flask App
# ==========================
app = Flask(__name__)

# ==========================
# Coinbase Spot Client Placeholder
# Replace with your actual CCXT client init
# ==========================
spot = None
# Example:
# import ccxt
# spot = ccxt.coinbasepro({
#     'apiKey': os.getenv('COINBASE_SPOT_KEY'),
#     'secret': os.getenv('COINBASE_SPOT_SECRET'),
#     'password': os.getenv('COINBASE_SPOT_PASSPHRASE')
# })

# ==========================
# Masking helpers
# ==========================
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

# ==========================
# AI Memory helpers
# ==========================
def load_ai_memory():
    try:
        with open(AI_MEMORY_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_ai_memory(mem):
    with open(AI_MEMORY_FILE, "w") as f:
        json.dump(mem, f, indent=2)

def update_ai_score(symbol, profit):
    mem = load_ai_memory()
    entry = mem.get(symbol, {"score": 1.0, "trades": 0, "profit": 0.0})
    factor = 1.05 if profit > 0 else 0.95
    entry["score"] *= factor
    entry["trades"] += 1
    entry["profit"] += profit
    mem[symbol] = entry
    save_ai_memory(mem)

# ==========================
# Daily top ticker scanner
# ==========================
def get_trend_score(symbol):
    # Simple placeholder: return 1.0 for now
    # Replace with SMA/RSI/trend calculation
    return 1.0

def daily_ai_scan(symbols):
    mem = load_ai_memory()
    top_symbols = []
    for s in symbols:
        trend = get_trend_score(s)
        hist_score = mem.get(s, {}).get("score", 1.0)
        combined = trend * hist_score
        top_symbols.append((s, combined))
    top_symbols.sort(key=lambda x: x[1], reverse=True)
    return top_symbols[:5]

# ==========================
# Webhook handler
# ==========================
@app.route("/webhook", methods=["POST"])
def webhook_post():
    try:
        raw = request.get_json(force=True, silent=True)
        masked = mask_payload(raw) if raw is not None else None
        print("📩 Signal Received (masked):", masked)

        if not raw:
            return jsonify({"status":"error","message":"invalid json or empty body"}), 400

        symbol = raw.get("symbol", "BTC-USD")
        side = raw.get("side", "buy")
        amount_raw = raw.get("amount", None)
        market_type = raw.get("market_type", "spot")

        if amount_raw is None:
            return jsonify({"status":"error","message":"missing amount"}), 400

        try:
            if isinstance(amount_raw, (int, float, Decimal)):
                amount = Decimal(str(amount_raw))
            else:
                amount = Decimal(str(amount_raw).strip())
            if amount <= 0:
                return jsonify({"status":"error","message":"amount must be > 0"}), 400
        except (InvalidOperation, ValueError):
            print("❌ Invalid amount value:", amount_raw)
            return jsonify({"status":"error","message":"invalid amount, must be numeric"}), 400

        if "/" in symbol:
            symbol = symbol.replace("/", "-")

        print(f"Parsed order -> symbol={symbol} side={side} amount={amount} DRY_RUN={DRY_RUN}")

        if DRY_RUN:
            simulated = {"symbol": symbol, "side": side, "amount": str(amount), "note": "dry-run (no real order placed)"}
            print("🟡 DRY_RUN simulated order:", simulated)
            return jsonify({"status":"dry-run","result": simulated}), 200

        if not spot:
            print("❌ Spot client not configured.")
            return jsonify({"status":"error","message":"spot client not configured"}), 500

        try:
            full_order = spot.create_market_order(symbol, side, float(amount))
            print("✅ Full order result:", full_order)
            # calculate realized profit placeholder
            realized_profit = float(full_order.get("filled_total", 0)) - float(full_order.get("cost", 0))
            update_ai_score(symbol, realized_profit)
            return jsonify({"status":"success","order": full_order}), 200
        except Exception as order_exc:
            print("❌ Exception placing order:", repr(order_exc))
            traceback.print_exc()
            return jsonify({"status":"error","message": str(order_exc)}), 500

    except Exception as e:
        print("❌ Unexpected exception in webhook_post:", repr(e))
        traceback.print_exc()
        return jsonify({"status":"error","message":"internal server error"}), 500

# ==========================
# Health check endpoint
# ==========================
@app.route("/", methods=["GET"])
def index():
    return jsonify({"status":"NijaBot live", "time": str(datetime.utcnow())})

# ==========================
# Run App
# ==========================
if __name__ == "__main__":
    print("✅ NijaBot initialized. Listening for webhooks...")
    app.run(host="0.0.0.0", port=8080)

# inside webhook_post()
raw = request.get_json(force=True, silent=True)
symbol = raw.get("symbol", "BTC-USD")
side = raw.get("side", "buy")
amount_raw = raw.get("amount", "0.0001")
ai_signal = float(raw.get("ai_signal", 1.0))

# Convert amount safely
from decimal import Decimal
amount = Decimal(str(amount_raw)) * Decimal(ai_signal)

# Normalize symbol
if "/" in symbol:
    symbol = symbol.replace("/", "-")

# Place trade automatically (spot or futures based on 'market_type')
market_type = raw.get("market_type", "spot")
client = spot if market_type=="spot" else futures_client

try:
    order = client.create_market_order(symbol, side, float(amount))
    print("✅ Order executed:", order)
except Exception as e:
    print("❌ Order failed:", repr(e))
