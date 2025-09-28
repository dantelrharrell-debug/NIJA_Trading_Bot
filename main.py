# main.py
import os, re, traceback
from decimal import Decimal, InvalidOperation
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import nija_ai
import os

TRADINGVIEW_SECRET = os.getenv("TRADINGVIEW_SECRET", "mysecret")

load_dotenv()

app = Flask(__name__)
DRY_RUN = os.getenv("DRY_RUN", "True").lower() == "true"

# Mask keys when printing
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
        return {k: mask_payload(v) for k,v in obj.items()}
    if isinstance(obj, list):
        return [mask_payload(v) for v in obj]
    if isinstance(obj, str):
        return mask_value(obj)
    return obj

@app.route("/webhook", methods=["POST"])
def webhook_post():
    try:
        raw = request.get_json(force=True, silent=True)
        masked = mask_payload(raw) if raw is not None else None
        print("📩 Signal Received (masked):", masked)

        if not raw:
            return jsonify({"status":"error","message":"invalid json or empty body"}), 400

        # Parse fields
        symbol = raw.get("symbol", "BTC-USD")
        if isinstance(symbol, str):
            symbol = symbol.replace("/", "-")
            # If symbol like DOGEUSD -> DOGE-USD
            if symbol.upper().endswith("USD") and "-" not in symbol:
                symbol = symbol[:-3] + "-USD"

        side = raw.get("side", "buy")
        amount_raw = raw.get("amount", None)  # could be qty or USD notional
        market_type = raw.get("market_type", "spot")
        ai_signal = raw.get("ai_signal", None)
        position_percent = raw.get("position_percent", None)

        if amount_raw is None:
            return jsonify({"status":"error","message":"missing amount"}), 400

        # Try parse amount as Decimal
        try:
            amount_dec = Decimal(str(amount_raw).strip())
        except Exception:
            return jsonify({"status":"error","message":"invalid amount format"}), 400

        # Detect if amount is USD notional or coin qty:
        # Heuristic: if amount > 10 and symbol endswith -USD -> treat as USD notional
        treat_as_usd = False
        if symbol.upper().endswith("-USD") and amount_dec > Decimal("10"):
            treat_as_usd = True

        # Convert USD to qty if needed
        if treat_as_usd:
            qty = nija_ai.convert_usd_to_qty(symbol, float(amount_dec))
            if qty is None:
                return jsonify({"status":"error","message":"failed to convert USD to quantity"}), 500
            amount_qty = Decimal(str(qty))
        else:
            amount_qty = amount_dec

        # Apply position_percent if provided (e.g., position_percent = "10" means 10%)
        if position_percent:
            try:
                scale = Decimal(str(position_percent)) / Decimal("100")
                if scale > 0:
                    amount_qty = amount_qty * scale
            except Exception:
                pass

        # Apply AI scaling based on history
        perf = nija_ai.last_trade_profit_percent(symbol)
        ai_multiplier = 1.0
        try:
            ai_multiplier = float(ai_signal) if ai_signal is not None else 1.0
        except Exception:
            ai_multiplier = 1.0

        if perf is not None:
            if perf > 0.5:
                ai_multiplier = min(ai_multiplier * 1.05, 2.0)
            elif perf < -0.5:
                ai_multiplier = max(ai_multiplier * 0.9, 0.1)

        try:
            final_amount = float(amount_qty * Decimal(str(ai_multiplier)))
        except Exception:
            final_amount = float(amount_qty)

        print(f"Parsed order -> symbol={symbol} side={side} amount={final_amount} market_type={market_type} DRY_RUN={DRY_RUN} perf={perf} ai_mul={ai_multiplier}")

        # If DRY_RUN, simulate and save entry
        if DRY_RUN:
            result = nija_ai.execute_trade(symbol, side, final_amount, market_type=market_type, dry_run=True)
            return jsonify({"status":"dry-run","result": result}), 200

        # Live: execute trade
        res = nija_ai.execute_trade(symbol, side, final_amount, market_type=market_type, dry_run=False)
        if res.get("error"):
            return jsonify({"status":"error","message": res["error"]}), 500
        return jsonify({"status":"success","result": res}), 200

    except Exception as e:
        print("❌ Unexpected exception in webhook_post:", repr(e))
        traceback.print_exc()
        return jsonify({"status":"error","message":"internal server error"}), 500

if __name__ == "__main__":
    print("✅ NijaBot webhook listening on /webhook")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
