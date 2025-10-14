#!/usr/bin/env python3
"""
nija_bot.py
NIJA trading bot — improved startup, mock mode fallback, safe sizing, and simple REST endpoints.

Usage:
- Ensure your start.sh activates the venv and exports USE_MOCK=False before running this file.
- Provide API_KEY and API_SECRET in Render environment variables to enable real Coinbase client.
- Optionally set WEBHOOK_SECRET to protect POST endpoints.

Author: Generated for Dante Harrell / NIJA UGUMU AMANI™
"""

import os
import sys
import traceback
import time
import math
import json
from typing import Dict, Any

from flask import Flask, request, jsonify

#!/usr/bin/env python3
import os
import sys
import traceback
from flask import Flask

# -------------------
# Determine mock mode (interpret env strictly)
# Treat absence of USE_MOCK as False (live) unless set to true/1/yes
# -------------------
_raw = os.getenv("USE_MOCK", "")
USE_MOCK = _raw.strip().lower() in ("1", "true", "yes")

if USE_MOCK:
    print("⚠️ Running in mock mode — Coinbase client not connected.")
else:
    try:
        import coinbase_advanced_py as cb
        print("✅ coinbase_advanced_py imported successfully.")

        API_KEY = os.getenv("API_KEY")
        API_SECRET = os.getenv("API_SECRET")

        if not API_KEY or not API_SECRET:
            raise ValueError("❌ Missing API_KEY or API_SECRET in environment")

        client = cb.Client(API_KEY, API_SECRET)
        print("🚀 Live Coinbase client connected.")

    except Exception as e:
        print("❌ Failed to connect live Coinbase client:")
        traceback.print_exc()
        USE_MOCK = True  # fallback to mock mode

# -------------------
# Logging helper
# -------------------
def log(*args, **kwargs):
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"[{ts}]", *args, **kwargs)
    sys.stdout.flush()

# -------------------
# Determine mock mode
# -------------------
USE_MOCK = os.getenv("USE_MOCK", "True").lower() == "true"
LIVE_TRADING = False  # will be set True only if client initialized and USE_MOCK is False

client = None

# -------------------
# Try real Coinbase client
# -------------------
if not USE_MOCK:
    try:
        import coinbase_advanced_py as cb  # expected package name from your environment
        log("✅ coinbase_advanced_py import OK.")
        API_KEY = os.getenv("API_KEY")
        API_SECRET = os.getenv("API_SECRET")

        if not API_KEY or not API_SECRET:
            log("⚠️ API_KEY or API_SECRET not found in environment — switching to mock mode.")
            USE_MOCK = True
        else:
            try:
                # Attempt to init the real client
                client = cb.Client(API_KEY, API_SECRET)
                LIVE_TRADING = True
                log("🚀 Coinbase client initialized — LIVE_TRADING enabled.")
            except Exception as e:
                log("❌ Failed to initialize Coinbase client:", e)
                traceback.print_exc()
                USE_MOCK = True
    except Exception as e:
        log("❌ coinbase_advanced_py not found or failed import:", e)
        traceback.print_exc()
        USE_MOCK = True
else:
    log("⚠️ USE_MOCK is set or defaulted to True — running in mock mode.")

# -------------------
# If mock mode, provide a simple MockClient that mirrors the methods we call
# -------------------
class MockClient:
    def __init__(self):
        # start with a pretend USD balance and some holdings
        self.balances = {"USD": 10000.0, "BTC": 0.05, "ETH": 0.3}
        # fake market prices
        self.prices = {"BTC-USD": 60000.0, "ETH-USD": 3500.0}
        log("🧪 MockClient initialized with balances:", self.balances)

    def get_account_balances(self) -> Dict[str, float]:
        # return a copy
        return dict(self.balances)

    def get_spot_price(self, product: str) -> float:
        return self.prices.get(product, 0.0)

    def place_market_order(self, product: str, side: str, size: float) -> Dict[str, Any]:
        """
        Simulate placing a market order.
        product e.g. 'BTC-USD', side 'buy'/'sell', size is in base currency for buy (USD for buy? we will interpret)
        We'll accept size as USD amount for 'buy' and as base coin amount for 'sell' for simplicity
        """
        price = self.get_spot_price(product)
        if price <= 0:
            raise ValueError("Unknown product/price in mock client")

        if side.lower() == "buy":
            usd_amount = size
            if self.balances.get("USD", 0) < usd_amount:
                raise ValueError("Insufficient USD balance in mock client")
            base_amount = usd_amount / price
            coin = product.split("-")[0]
            self.balances["USD"] -= usd_amount
            self.balances[coin] = self.balances.get(coin, 0) + base_amount
            return {"status": "filled", "side": "buy", "product": product, "filled_size": base_amount, "price": price}
        else:
            coin = product.split("-")[0]
            base_amount = size
            if self.balances.get(coin, 0) < base_amount:
                raise ValueError("Insufficient coin balance in mock client")
            usd_amount = base_amount * price
            self.balances[coin] -= base_amount
            self.balances["USD"] = self.balances.get("USD", 0) + usd_amount
            return {"status": "filled", "side": "sell", "product": product, "filled_size": base_amount, "price": price}

    def get_portfolio_value_usd(self) -> float:
        """Rough total portfolio value in USD."""
        total = self.balances.get("USD", 0.0)
        for coin, amt in list(self.balances.items()):
            if coin == "USD":
                continue
            price = self.get_spot_price(f"{coin}-USD")
            total += amt * price
        return total

# initialize mock client if needed
if USE_MOCK:
    client = MockClient()

# -------------------
# Position sizing defaults (user preference: min 2% max 10%)
# these can be overridden by environment variables
# -------------------
MIN_PCT_ENV = float(os.getenv("MIN_POSITION_PCT", "0.02"))   # 2%
MAX_PCT_ENV = float(os.getenv("MAX_POSITION_PCT", "0.10"))   # 10%
MIN_PCT = max(0.0, min(1.0, MIN_PCT_ENV))
MAX_PCT = max(MIN_PCT, min(1.0, MAX_PCT_ENV))

log(f"Position sizing configured: MIN_PCT={MIN_PCT:.2%}, MAX_PCT={MAX_PCT:.2%}")

# -------------------
# Helpers: sizing + safe_order
# -------------------
def get_account_usd_value() -> float:
    """Return a USD value representing the account equity; client may provide direct method or we estimate."""
    try:
        # if client has helper get_portfolio_value_usd, use it
        if hasattr(client, "get_portfolio_value_usd"):
            return float(client.get_portfolio_value_usd())
        # otherwise attempt to call a common 'get_account_balances' and compute
        balances = client.get_account_balances()
        usd = float(balances.get("USD", 0.0))
        # try common coins
        for coin in ["BTC", "ETH"]:
            if coin in balances:
                price = client.get_spot_price(f"{coin}-USD") if hasattr(client, "get_spot_price") else 0.0
                usd += balances[coin] * (price or 0.0)
        return usd
    except Exception as e:
        log("⚠️ Couldn't compute account USD value:", e)
        return 0.0

def compute_allocation_amount(percent: float = None) -> float:
    """
    Determine USD amount to allocate based on percent OR using default envelope between MIN_PCT and MAX_PCT.
    If percent provided, it's interpreted as fraction (0.05 => 5%).
    """
    account_value = get_account_usd_value()
    if account_value <= 0:
        raise ValueError("Account value unknown or zero")

    if percent is None:
        # default to min_pct for safety
        pct = MIN_PCT
    else:
        pct = float(percent)
        # clamp pct to min/max
        if pct < MIN_PCT:
            log(f"Requested pct {pct:.2%} below MIN_PCT — clamping to {MIN_PCT:.2%}")
            pct = MIN_PCT
        elif pct > MAX_PCT:
            log(f"Requested pct {pct:.2%} above MAX_PCT — clamping to {MAX_PCT:.2%}")
            pct = MAX_PCT

    usd_amount = account_value * pct
    usd_amount = round(usd_amount, 2)
    log(f"compute_allocation_amount -> account_value ${account_value:.2f}, pct {pct:.2%}, usd_amount ${usd_amount}")
    return usd_amount

def place_market_order_safe(product: str, side: str, usd_amount: float = None, base_amount: float = None):
    """
    Place an order safely:
    - For buy: we accept usd_amount (USD to spend) or compute from percent envelope
    - For sell: base_amount (coins) should be provided (or computed from holdings)
    """
    if side.lower() not in ("buy", "sell"):
        raise ValueError("side must be 'buy' or 'sell'")

    # Buy path: we expect usd_amount
    if side.lower() == "buy":
        if usd_amount is None:
            raise ValueError("usd_amount required for buy orders")
        # If live trading disabled, throw if LIVE_TRADING False
        if LIVE_TRADING is False:
            log("⚠️ LIVE_TRADING is False — order will NOT be sent to exchange. Returning simulated response.")
            return {"simulated": True, "product": product, "side": "buy", "usd": usd_amount}
        # real client: attempt an order
        try:
            # many clients expect size in base coin or USD depending on method.
            # Here we call a hypothetical place_market_order or place_market_order_usd.
            if hasattr(client, "place_market_order"):
                # The real coinbase_advanced_py API may differ — adapt to your real client
                return client.place_market_order(product=product, side="buy", usd_size=usd_amount)
            elif hasattr(client, "place_market_order_usd"):
                return client.place_market_order_usd(product, usd_amount, side="buy")
            else:
                # best-effort: call place_market_order with usd amount
                return client.place_market_order(product, "buy", usd_amount)
        except Exception as e:
            log("❌ Error placing real buy order:", e)
            traceback.print_exc()
            raise

    # Sell path: we expect base_amount
    if side.lower() == "sell":
        if base_amount is None:
            raise ValueError("base_amount required for sell orders")
        if LIVE_TRADING is False:
            log("⚠️ LIVE_TRADING is False — sell simulated.")
            return {"simulated": True, "product": product, "side": "sell", "base": base_amount}
        try:
            if hasattr(client, "place_market_order"):
                return client.place_market_order(product=product, side="sell", size=base_amount)
            else:
                return client.place_market_order(product, "sell", base_amount)
        except Exception as e:
            log("❌ Error placing real sell order:", e)
            traceback.print_exc()
            raise

# -------------------
# Flask app
# -------------------
app = Flask("nija_bot")

# get webhook secret if set
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "").strip()

def is_authorized(req) -> bool:
    """Simple bearer or header secret check"""
    if not WEBHOOK_SECRET:
        # no secret configured — allow by default (not recommended for prod)
        return True
    # check header X-Webhook-Secret
    header = req.headers.get("X-Webhook-Secret") or req.headers.get("X-Secret")
    if header and header == WEBHOOK_SECRET:
        return True
    # check Bearer token
    auth = req.headers.get("Authorization", "")
    if auth.startswith("Bearer ") and auth.split(" ", 1)[1].strip() == WEBHOOK_SECRET:
        return True
    return False

@app.route("/", methods=["GET", "HEAD"])
def health():
    payload = {
        "status": "ok",
        "live_trading": LIVE_TRADING,
        "use_mock": USE_MOCK,
        "client_present": client is not None
    }
    return jsonify(payload), 200

@app.route("/balances", methods=["GET"])
def balances():
    try:
        b = client.get_account_balances()
        return jsonify({"balances": b}), 200
    except Exception as e:
        log("⚠️ Error getting balances:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/value", methods=["GET"])
def portfolio_value():
    try:
        val = get_account_usd_value()
        return jsonify({"portfolio_usd": val}), 200
    except Exception as e:
        log("⚠️ Error computing portfolio value:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/trade", methods=["POST"])
def trade():
    """
    POST /trade
    Headers: X-Webhook-Secret: <secret>  (if configured)
    Body JSON:
    {
      "product": "BTC-USD",
      "side": "buy" | "sell",
      "percent": 0.05           # optional - fraction of account equity (for buys). Will be clamped to MIN/MAX.
      "usd_amount": 500.0       # optional - explicit USD amount to spend (overrides percent)
      "base_amount": 0.001      # optional - for sells, specify base coin amount
    }
    """
    if not is_authorized(request):
        return jsonify({"error": "unauthorized"}), 401

    try:
        payload = request.get_json(force=True)
    except Exception as e:
        return jsonify({"error": "invalid json", "details": str(e)}), 400

    product = payload.get("product")
    side = (payload.get("side") or "").lower()
    if not product or side not in ("buy", "sell"):
        return jsonify({"error": "product and side ('buy' or 'sell') required"}), 400

    # determine amounts
    usd_amount = payload.get("usd_amount")
    base_amount = payload.get("base_amount")
    percent = payload.get("percent")

    try:
        if side == "buy":
            if usd_amount is None:
                # compute from percent (or defaults)
                alloc_usd = compute_allocation_amount(percent)
            else:
                alloc_usd = float(usd_amount)
                # clamp by MIN/MAX relative to account if needed
                account_val = get_account_usd_value()
                min_allowed = account_val * MIN_PCT
                max_allowed = account_val * MAX_PCT
                if alloc_usd < min_allowed:
                    log(f"Buy usd_amount ${alloc_usd} below min ${min_allowed:.2f} — clamping.")
                    alloc_usd = round(min_allowed, 2)
                if alloc_usd > max_allowed:
                    log(f"Buy usd_amount ${alloc_usd} above max ${max_allowed:.2f} — clamping.")
                    alloc_usd = round(max_allowed, 2)

            resp = place_market_order_safe(product=product, side="buy", usd_amount=alloc_usd)
            return jsonify({"result": resp}), 200

        else:  # sell
            if base_amount is None:
                return jsonify({"error": "base_amount required for sell orders"}), 400
            resp = place_market_order_safe(product=product, side="sell", base_amount=float(base_amount))
            return jsonify({"result": resp}), 200

    except Exception as e:
        log("❌ Exception in /trade:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/simulate", methods=["POST"])
def simulate():
    """
    Simulate an order without touching live trading. Useful for debugging allocation.
    Body JSON: same as /trade
    """
    try:
        payload = request.get_json(force=True)
    except Exception as e:
        return jsonify({"error": "invalid json", "details": str(e)}), 400

    product = payload.get("product")
    side = (payload.get("side") or "").lower()
    percent = payload.get("percent")
    usd_amount = payload.get("usd_amount")
    base_amount = payload.get("base_amount")

    if side not in ("buy", "sell") or not product:
        return jsonify({"error": "product and side required"}), 400

    try:
        if side == "buy":
            if usd_amount is None:
                usd = compute_allocation_amount(percent)
            else:
                usd = float(usd_amount)
            return jsonify({"simulated_order": {"product": product, "side": "buy", "usd": usd}}), 200
        else:
            if base_amount is None:
                return jsonify({"error": "base_amount required for sell simulation"}), 400
            return jsonify({"simulated_order": {"product": product, "side": "sell", "base": float(base_amount)}}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------
# Graceful startup message
# -------------------
if __name__ == "__main__":
    # If execute directly, make sure Flask uses host 0.0.0.0 and port from env (Render passes PORT)
    port = int(os.getenv("PORT", "10000"))
    log("🟢 NIJA BOT starting; LIVE_TRADING =", LIVE_TRADING)
    # Run Flask dev server — Render's start.sh should exec this file in the activated venv
    app.run(host="0.0.0.0", port=port)
