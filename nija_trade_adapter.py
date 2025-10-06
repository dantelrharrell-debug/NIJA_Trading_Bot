"""
NIJA: Coinbase Advanced SDK adapter + live-submit toggle
Uses the official coinbase-advanced-py RESTClient API:
  - get_accounts()
  - get_product(product_id)
  - market_order_buy(...) / market_order_sell(...) or create_order(...)
  - list_orders()
Docs examples: coinbase-advanced-py README / SDK quickstart.
(See citations included in chat for reference.)
"""

import os
import math
import time
from json import dumps
from coinbase.rest import RESTClient   # official SDK

# ---------- CONFIG ----------
DRY_RUN = True            # True => won't submit orders. Set False to enable live submits.
MIN_PCT = 0.02            # 2%
MAX_PCT = 0.10            # 10%
MIN_TRADE_USD = 1.00      # floor in USD (adjust to actual pair minimums)
FEE_BUFFER = 0.005        # 0.5% safety buffer
PRICE_PRECISION = 2       # cents
ASSET_PRECISION = {
    "BTC-USD": 8,
    "ETH-USD": 6,
    "DEFAULT": 6
}
# Place your API creds in env vars for safety
API_KEY = os.getenv("COINBASE_API_KEY")        # e.g. "organizations/{org_id}/apiKeys/{key_id}"
API_SECRET = os.getenv("COINBASE_API_SECRET")  # the full PEM private key text string
# ----------------------------

def init_client():
    if not API_KEY or not API_SECRET:
        raise RuntimeError("Missing COINBASE_API_KEY or COINBASE_API_SECRET environment variables.")
    # The RESTClient constructor uses (api_key=..., api_secret=...)
    client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
    return client

def get_usd_equity(client):
    """
    Uses client.get_accounts() to sum USD/USDC available balances.
    Returns a float (USD-equivalent available).
    """
    accounts = client.get_accounts()  # returns a custom response object
    # convert to dict/list for safe access
    acc_list = accounts.to_dict().get("accounts", []) if hasattr(accounts, "to_dict") else accounts
    usd_equity = 0.0
    for a in acc_list:
        currency = a.get("currency") or a.get("asset") or a.get("code")
        # available balance field may be 'available_balance' or 'available'
        # the SDK uses structures; use defensive parsing:
        avail = None
        if "available_balance" in a and isinstance(a["available_balance"], dict):
            avail = a["available_balance"].get("value")
        elif "available" in a:
            avail = a.get("available")
        elif "balance" in a and isinstance(a["balance"], dict):
            avail = a["balance"].get("value")
        elif "balance" in a:
            avail = a.get("balance")
        if avail is None:
            continue
        try:
            bal = float(avail)
        except Exception:
            # if nested structure with string, try to extract
            try:
                bal = float(str(avail))
            except Exception:
                bal = 0.0
        if currency in ("USD", "USDC", "USD-C"):
            usd_equity += bal
        # NOTE: we ignore non-USD assets for now; could convert via product prices if desired
    return usd_equity

def compute_trade_size(account_equity, desired_pct, min_trade=MIN_TRADE_USD, fee_buffer=FEE_BUFFER):
    pct = max(MIN_PCT, min(MAX_PCT, desired_pct))
    raw = account_equity * pct
    raw_after_fees = raw * (1.0 - fee_buffer)
    final = max(raw_after_fees, min_trade)
    return round(final, PRICE_PRECISION)

def get_price(client, product_id):
    """
    Use client.get_product(product_id) to get product.price
    Returns float price (USD per base unit).
    """
    product = client.get_product(product_id)
    # product may be a custom object - try dot then dict
    if hasattr(product, "price"):
        return float(product.price)
    p = product.to_dict() if hasattr(product, "to_dict") else product
    return float(p.get("price") or p.get("last") or 0.0)

def usd_to_base_amount(usd_amount, price, product_id):
    precision = ASSET_PRECISION.get(product_id, ASSET_PRECISION["DEFAULT"])
    base_amount = usd_amount / price if price > 0 else 0.0
    # floor to avoid buying more than quote_size worth
    rounded = math.floor(base_amount * (10 ** precision)) / (10 ** precision)
    return rounded

def build_and_submit_order(client, product_id, side, trade_usd, prefer_quote=True, order_type="market", client_order_id=""):
    """
    prefer_quote=True uses quote_size (spend USD); otherwise converts to base size.
    Uses official SDK methods: market_order_buy / market_order_sell or generic create_order wrapper.
    """
    if prefer_quote and order_type == "market" and side.lower() == "buy":
        # SDK helper for a market buy using quote_size
        payload = {
            "client_order_id": client_order_id or "",
            "product_id": product_id,
            "quote_size": str(round(trade_usd, PRICE_PRECISION))
        }
        print("[NIJA] Prepared market buy (quote_size):", payload)
        if DRY_RUN:
            return {"status":"dry_run", "payload": payload}
        # submit using market_order_buy
        resp = client.market_order_buy(**payload)  # example from SDK README
    else:
        # convert to base size and place a market order via market_order()
        price = get_price(client, product_id)
        base_size = usd_to_base_amount(trade_usd, price, product_id)
        payload = {
            "client_order_id": client_order_id or "",
            "product_id": product_id,
            "base_size": str(base_size)
        }
        print("[NIJA] Prepared market buy/sell (base_size):", payload)
        if DRY_RUN:
            return {"status":"dry_run", "payload": payload}
        if order_type == "market":
            if side.lower() == "buy":
                resp = client.market_order_buy(**payload)
            else:
                resp = client.market_order_sell(**payload)
        else:
            # fallback: call create_order (more generic) - example structure depends on SDK
            # We'll attempt create_order with product_id + order configuration (SDK follows similar shape)
            ord_req = {
                "client_order_id": client_order_id or "",
                "product_id": product_id,
                "order_configuration": {
                    "market_order": {"quote_size": str(round(trade_usd, PRICE_PRECISION))}
                }
            }
            resp = client.create_order(ord_req)  # may need adjustment per SDK shape
    # return the SDK response object (custom type) - convert to dict for easy logging
    try:
        return {"status":"submitted", "response": resp.to_dict() if hasattr(resp, "to_dict") else resp}
    except Exception:
        return {"status":"submitted", "response": str(resp)}

def confirm_recent_orders(client, limit=5):
    """
    Use client.list_orders(limit=...) to show recent orders (open/filled)
    """
    resp = client.list_orders(limit=limit)
    return resp.to_dict() if hasattr(resp, "to_dict") else resp

# ---------------- Sample usage flow ----------------
if __name__ == "__main__":
    # Safety: set DRY_RUN True until you're ready
    print("DRY_RUN =", DRY_RUN)
    client = None
    try:
        client = init_client()
    except Exception as e:
        print("Client init failed:", e)
        print("Exiting. Set COINBASE_API_KEY and COINBASE_API_SECRET in environment and try again.")
        raise SystemExit(1)

    equity = get_usd_equity(client)
    print(f"Available USD equity: ${equity:.2f}")

    # Example: try a 5% allocation on BTC-USD
    desired_pct = 0.05
    trade_usd = compute_trade_size(equity, desired_pct)
    print(f"Computed trade size for {int(desired_pct*100)}% -> ${trade_usd:.2f}")

    # Build and submit (or dry-run) a market buy for BTC-USD
    result = build_and_submit_order(client, product_id="BTC-USD", side="buy", trade_usd=trade_usd, prefer_quote=True)
    print("Order result:", dumps(result, indent=2))

    # Optionally show recent orders
    time.sleep(0.5)
    try:
        recent = confirm_recent_orders(client, limit=5)
        print("Recent orders:", dumps(recent, indent=2))
    except Exception as e:
        print("Failed to fetch recent orders:", e)
