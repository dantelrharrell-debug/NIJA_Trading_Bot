#!/usr/bin/env python3
import sys
import os

# Force Render to use the virtual environment packages
sys.path.insert(0, os.path.join(os.getcwd(), ".venv/lib/python3.13/site-packages"))

import coinbase_advanced_py as cb
from flask import Flask, request, abort
import json

#!/usr/bin/env python3
import os
import json
from flask import Flask, request, abort
import coinbase_advanced_py as cb

# --- Load environment ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

if not API_KEY or not API_SECRET or not WEBHOOK_SECRET:
    raise SystemExit("❌ API_KEY, API_SECRET, or WEBHOOK_SECRET not set!")

# --- Initialize Coinbase Advanced Client ---
client = cb.Client(API_KEY, API_SECRET)

# --- Flask Web Server ---
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    # Verify webhook secret
    secret = request.headers.get("X-Webhook-Secret")
    if secret != WEBHOOK_SECRET:
        abort(403)

    data = request.json
    print("📩 Webhook received:", data)

    try:
        symbol = data["symbol"]
        action = data["action"]
        amount = float(data["amount"])
        leverage = int(data.get("leverage", 1))
        take_profit = data.get("take_profit")
        stop_loss = data.get("stop_loss")

        # --- Open position ---
        order = client.create_futures_order(
            symbol=symbol,
            side=action.lower(),
            type="market",
            size=amount,
            leverage=leverage
        )
        print("✅ Position opened:", order)

        # --- Optional: TP/SL ---
        if take_profit or stop_loss:
            tp_sl_order = client.create_futures_tp_sl_order(
                symbol=symbol,
                size=amount,
                take_profit=take_profit,
                stop_loss=stop_loss
            )
            print("🎯 TP/SL set:", tp_sl_order)

        return {"status": "success", "order": order}, 200

    except Exception as e:
        print("❌ Error executing trade:", e)
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
