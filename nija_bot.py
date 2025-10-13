#!/usr/bin/env python3
# nija_live_bot.py
"""
NIJA Live Trading Bot
- Receives TradingView webhooks at /webhook
- Verifies signature with WEBHOOK_SECRET
- Calculates position size (2% - 10% of USD equity)
- Executes market orders on Coinbase (via coinbase_advanced_py)
- Default mode is DRY RUN. Set LIVE=true to actually place orders.
"""

import os
import json
import hmac
import hashlib
import time
import csv
from datetime import datetime, timezone
from threading import Lock

from flask import Flask, request, jsonify

# Try import coinbase sdk; fail loudly if not present
try:
    import coinbase_advanced_py as cb
except Exception as e:
    raise SystemExit(f"Missing dependency: coinbase_advanced_py. Install and re-run. ({e})")

# -----------------------
# Configuration (env)
# -----------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")  # required for signature verification
LIVE_MODE = os.getenv("LIVE", "false").lower() == "true"  # must be "true" to place orders
MIN_PERCENT = float(os.getenv("MIN_POSITION_PCT", "2")) / 100.0   # default 2%
MAX_PERCENT = float(os.getenv("MAX_POSITION_PCT", "10")) / 100.0  # default 10%
MIN_TRADE_USD = float(os.getenv("MIN_TRADE_USD", "1.0"))         # don't place < this USD
RATE_LIMIT_SEC = float(os.getenv("RATE_LIMIT_SEC", "1.0"))       # min seconds between orders (basic guard)
LOG_FILE = os.getenv("TRADES_LOG", "trades_log.csv")

if not API_KEY or not API_SECRET:
    raise SystemExit("Missing API_KEY/API_SECRET environment variables. Set them and re-run.")

if not WEBHOOK_SECRET:
    print("⚠️  Warning: WEBHOOK_SECRET is empty. It's recommended to set a webhook secret for security.")

# -----------------------
# Coinbase client
# -----------------------
try:
    client = cb.Client(API_KEY, API_SECRET)
    print("✅ Coinbase client initialized.")
except Exception as e:
    raise SystemExit(f"Failed to create Coinbase client: {e}")

# -----------------------
# Flask app
# -----------------------
app = Flask(__name__)
last_order_ts = 0.0
order_lock = Lock()

# Ensure log file has header
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_utc", "symbol", "signal", "usd_amount", "order_id", "status", "notes"])

# -----------------------
# Helpers
# -----------------------
def now_utc_iso():
    return datetime.now(timezone.utc).isoformat()

def verify_signature(payload_bytes: bytes, received_sig: str) -> bool:
    """
    HMAC-SHA256 of payload using WEBHOOK_SECRET.
    TradingView or your webhook sender should generate this header.
    Header name expected: X-Signature
    """
    if not WEBHOOK_SECRET:
        # skip verification if secret not set (not recommended)
        return True
    try:
        computed = hmac.new(WEBHOOK_SECRET.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, received_sig)
    except Exception:
        return False

def get_usd_balance():
    """
    Returns available USD balance as float (0.0 if none / on error).
    """
    try:
        accounts = client.get_accounts()
        for a in accounts:
            # account object shape may vary; handle common shapes
            cur = getattr(a, "currency", None) or a.get("currency") if isinstance(a, dict) else None
            bal = getattr(a, "balance", None) or a.get("balance") if isinstance(a, dict) else None
            # balance could be object with 'amount' etc
            if cur == "USD":
                if isinstance(bal, dict):
                    return float(bal.get("amount", 0))
                try:
                    return float(bal)
                except Exception:
                    # some libs return a small object; try str conversion
                    return float(str(bal))
    except Exception as e:
        print(f"[get_usd_balance] Error reading accounts: {e}")
    return 0.0

def calculate_position_amount(usd_balance: float) -> float:
    """
    Use aggressive-but-safe rule: pick between MIN_PERCENT and MAX_PERCENT of balance.
    We choose MAX_PERCENT by default for aggressive behavior.
    """
    # choose max percent for aggressive sizing
    usd_amount = usd_balance * MAX_PERCENT
    # floor to 2 decimal places (USD cents)
    usd_amount = float(int(usd_amount * 100)) / 100.0
    if usd_amount < MIN_TRADE_USD:
        return 0.0
    return usd_amount

def place_market_order(symbol: str, side: str, usd_amount: float):
    """
    Place a market order on Coinbase using `funds` (USD).
    Wrap in try/except and return order info or raise.
    """
    # Basic guard: avoid too-frequent orders
    global last_order_ts
    with order_lock:
        now_ts = time.time()
        if now_ts - last_order_ts < RATE_LIMIT_SEC:
            raise RuntimeError("Rate limit guard: attempted order too soon after previous order.")
        last_order_ts = now_ts

    # Some client APIs accept 'funds' or 'size'; prefer 'funds' for USD-based amount.
    order = None
    try:
        # Common coinbase-advanced-py method: create_order with 'funds' for USD amount
        order = client.create_order(
            product_id=symbol,
            side=side,
            type="market",
            funds=str(usd_amount)  # place market buy/sell for USD amount
        )
        return order
    except Exception as e_create:
        # Try alternate method name if library differs
        try:
            order = client.place_order(
                product_id=symbol,
                side=side,
                order_type="market",
                funds=str(usd_amount)
            )
            return order
        except Exception as e_place:
            # If both fail, surface the original create exception for context
            raise RuntimeError(f"Order failed: create_error={e_create}, place_error={e_place}")

def log_trade(symbol, signal, usd_amount, order_id, status, notes=""):
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([now_utc_iso(), symbol, signal, usd_amount, order_id, status, notes])

# -----------------------
# Webhook endpoint
# -----------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data or b""
    received_sig = request.headers.get("X-Signature", "") or request.headers.get("X-Signature-256", "")

    if not verify_signature(payload, received_sig):
        print("❌ Webhook signature verification failed.")
        return "Invalid signature", 403

    try:
        data = json.loads(payload)
    except Exception as e:
        print(f"❌ Invalid JSON payload: {e}")
        return "Bad request", 400

    # Expected payload keys: symbol, signal (buy/sell), optionally size_usd
    symbol = data.get("symbol") or data.get("ticker") or "BTC-USD"
    signal = (data.get("signal") or data.get("side") or "").lower()
    provided_size = data.get("size_usd")  # optional override

    if signal not in ("buy", "sell"):
        print(f"❌ Invalid signal: {signal}")
        return "Invalid signal", 400

    # Get available USD
    usd_balance = get_usd_balance()
    if usd_balance <= 0:
        notes = "No USD balance"
        print(f"⚠ {notes}")
        log_trade(symbol, signal, 0.0, "", "failed", notes)
        return jsonify({"status": "failed", "reason": notes}), 200

    # Decide trade amount
    if provided_size:
        try:
            usd_amount = float(provided_size)
        except Exception:
            usd_amount = calculate_position_amount(usd_balance)
    else:
        usd_amount = calculate_position_amount(usd_balance)

    if usd_amount < MIN_TRADE_USD:
        notes = f"Calculated trade < MIN_TRADE_USD ({usd_amount} < {MIN_TRADE_USD})"
        print(f"⚠ {notes}")
        log_trade(symbol, signal, usd_amount, "", "skipped", notes)
        return jsonify({"status": "skipped", "reason": notes}), 200

    # If not live mode, simulate and return details
    if not LIVE_MODE:
        notes = "DRY RUN (LIVE not enabled)"
        print(f"🧪 DRY RUN -> Would {signal.upper()} {symbol} for ${usd_amount:.2f}.")
        log_trade(symbol, signal, usd_amount, "", "dry_run", notes)
        return jsonify({"status": "dry_run", "symbol": symbol, "signal": signal, "usd_amount": usd_amount}), 200

    # LIVE MODE: attempt order
    try:
        print(f"🚀 LIVE -> Placing market {signal.upper()} for {symbol}, USD ${usd_amount:.2f}")
        order = place_market_order(symbol, signal, usd_amount)
        # order object shape varies; attempt extract id
        order_id = getattr(order, "id", None) or (order.get("id") if isinstance(order, dict) else str(order))
        print(f"✅ Order placed. id={order_id}")
        log_trade(symbol, signal, usd_amount, order_id, "executed", "live order placed")
        return jsonify({"status": "executed", "order_id": order_id}), 200
    except Exception as e:
        notes = f"order_error: {e}"
        print(f"❌ LIVE order failed: {e}")
        log_trade(symbol, signal, usd_amount, "", "failed", notes)
        return jsonify({"status": "failed", "error": str(e)}), 500

# Health check
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "live_mode": LIVE_MODE}), 200

# -----------------------
# Run server
# -----------------------
if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    print("NIJA Live Bot starting up...")
    print(f" LIVE_MODE = {LIVE_MODE} (set env LIVE=true to enable real orders)")
    print(f" Listening for webhooks on /webhook (port {port})")
    app.run(host=host, port=port)
