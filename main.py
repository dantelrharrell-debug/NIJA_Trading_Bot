from flask import Flask, request, jsonify
from decimal import Decimal, InvalidOperation
import re, traceback, json
from nija_ai_scan import scan_market

app = Flask(__name__)
DRY_RUN = True  # set False to trade live

KEY_RE = re.compile(r'^[A-Za-z0-9\-_]{20,}$')  # mask keys

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

def get_ai_score(symbol):
    """Fetch AI score from saved daily scan"""
    try:
        with open("ai_top_tickers.json") as f:
            top = json.load(f)
        for t in top:
            if t['symbol'].replace("-", "/") == symbol:
                return Decimal(str(t['ai_score']))
    except:
        pass
    return Decimal("1.0")  # default multiplier if no AI data

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
            print("❌ Invalid amount:", amount_raw)
            return jsonify({"status":"error","message":"invalid amount, must be numeric"}), 400

        if "/" in symbol:
            symbol = symbol.replace("/", "-")

        ai_multiplier = get_ai_score(symbol)
        amount *= ai_multiplier  # adjust amount with AI score

        print(f"Parsed order -> symbol={symbol} side={side} amount={amount} DRY_RUN={DRY_RUN} AI={ai_multiplier}")

        if DRY_RUN:
            simulated = {"symbol": symbol, "side": side, "amount": str(amount), "note": "dry-run (no real order)"}
            print("🟡 DRY_RUN simulated order:", simulated)
            return jsonify({"status":"dry-run","result": simulated}), 200

        if market_type == "spot":
            from ccxt import coinbase
            spot = coinbase({"apiKey": "YOUR_SPOT_KEY", "secret": "YOUR_SPOT_SECRET"})
            try:
                full_order = spot.create_market_order(symbol, side, float(amount))
                print("✅ Spot order result:", full_order)
                return jsonify({"status":"success","order": full_order}), 200
            except Exception as e:
                print("❌ Spot order exception:", e)
                return jsonify({"status":"error","message": str(e)}), 500

        elif market_type == "futures":
            from ccxt import coinbasepro
            futures = coinbasepro({"apiKey": "YOUR_FUTURES_KEY", "secret": "YOUR_FUTURES_SECRET"})
            try:
                full_order = futures.create_market_order(symbol, side, float(amount))
                print("✅ Futures order result:", full_order)
                return jsonify({"status":"success","order": full_order}), 200
            except Exception as e:
                print("❌ Futures order exception:", e)
                return jsonify({"status":"error","message": str(e)}), 500

        else:
            return jsonify({"status":"error","message":"unknown market_type"}), 400

    except Exception as e:
        print("❌ Unexpected exception:", e)
        traceback.print_exc()
        return jsonify({"status":"error","message":"internal server error"}), 500
