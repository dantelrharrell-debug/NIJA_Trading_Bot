# test_coinbase_live.py
# Safe diagnostics for Coinbase spot + futures (ccxt)
# By default: READ-ONLY (fetch time, balances, open orders).
# Uncomment the "PLACE TEST ORDER" section only when you're ready to actually send live orders.

import os
import time
import ccxt

def make_exchange_from_env(prefix, default_id='coinbasepro'):
    """
    prefix: e.g. 'COINBASE_SPOT' or 'COINBASE_FUTURES'
    default_id: exchange id to try (adjust if your setup uses another ccxt id)
    """
    api_key = os.getenv(prefix + "_KEY", "").strip()
    secret = os.getenv(prefix + "_SECRET", "").strip()
    passphrase = os.getenv(prefix + "_PASSPHRASE", "").strip()
    exchange_id = os.getenv(prefix + "_EXCHANGE_ID", default_id).strip()  # optional override

    if not api_key or not secret:
        raise ValueError(f"{prefix} keys not found in environment. Set {prefix}_KEY and {prefix}_SECRET")

    params = {}
    # ccxt coinbasepro uses 'password' for passphrase
    if passphrase:
        params['password'] = passphrase

    ex_class = getattr(ccxt, exchange_id, None)
    if not ex_class:
        raise ValueError(f"ccxt does not have an exchange called '{exchange_id}'. Check {prefix}_EXCHANGE_ID")

    ex = ex_class({
        'apiKey': api_key,
        'secret': secret,
        'enableRateLimit': True,
        **({'password': passphrase} if passphrase else {})
    })
    # optional: set a specific API base if you use sandbox vs live, via env var:
    base_url = os.getenv(prefix + "_API_URL", "")
    if base_url:
        ex.urls['api'] = base_url
    return ex

def run_checks():
    print("=== STARTING COINBASE LIVE CHECKS ===")
    # Spot
    try:
        spot = make_exchange_from_env('COINBASE_SPOT', default_id='coinbasepro')
        print("\n--- SPOT (coinbasepro by default) ---")
        print("Server time:", spot.milliseconds())
        bal = spot.fetch_balance()
        print("Spot total balances (non-zero):")
        for k,v in bal.get('total', {}).items():
            if v and float(v) != 0:
                print(f"  {k}: {v}")
        open_orders = spot.fetch_open_orders()
        print(f"Spot open orders: {len(open_orders)}")
        for o in open_orders[:10]:
            print(" ", o.get('id'), o.get('symbol'), o.get('status'), o.get('info',{}))
    except Exception as e:
        print("SPOT CHECK ERROR:", repr(e))

    # Futures
    try:
        futures = make_exchange_from_env('COINBASE_FUTURES', default_id='coinbasepro')
        print("\n--- FUTURES (uses same ccxt id by default; override with COINBASE_FUTURES_EXCHANGE_ID) ---")
        print("Server time:", futures.milliseconds())
        bal_f = futures.fetch_balance()
        print("Futures total balances (non-zero):")
        for k,v in bal_f.get('total', {}).items():
            if v and float(v) != 0:
                print(f"  {k}: {v}")
        open_orders_f = futures.fetch_open_orders()
        print(f"Futures open orders: {len(open_orders_f)}")
        for o in open_orders_f[:10]:
            print(" ", o.get('id'), o.get('symbol'), o.get('status'), o.get('info',{}))
    except Exception as e:
        print("FUTURES CHECK ERROR:", repr(e))

    print("\n=== DIAGNOSTIC COMPLETE ===")

    # -------------------------
    # OPTIONAL: place a tiny market buy (UNCOMMENT to run live)
    # WARNING: This will place a real live order if enabled. Use small amounts.
    # -------------------------
    """
    try:
        symbol_spot = "BTC/USD"  # adjust to your market naming, e.g. "BTC-USD" or "BTC/USD" depending on the exchange
        amount = 0.0001  # tiny amount of BTC (adjust for your exchange min)
        print("\nPlacing a tiny spot market buy (UNCOMMENTED SECTION) ...")
        order = spot.create_order(symbol_spot, 'market', 'buy', amount)
        print("Placed spot order:", order)
        print("Cancelling spot order (if still open)...")
        try:
            spot.cancel_order(order['id'], symbol_spot)
            print("Cancelled.")
        except Exception as e2:
            print("Cancel spot order error (might be filled):", e2)
    except Exception as e:
        print("Error placing spot test order:", e)
    """

if __name__ == "__main__":
    run_checks()
