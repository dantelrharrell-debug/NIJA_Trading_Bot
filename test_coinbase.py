# test_coinbase.py
# Simple safe tester for Coinbase (reads keys from .env and prints balances)
# Requires: pip install python-dotenv ccxt

from dotenv import load_dotenv
import os
import ccxt
import sys

load_dotenv()  # loads .env in same folder

def make_exchange(key_env, secret_env, pass_env):
    api_key = os.getenv(key_env, "").strip()
    api_secret = os.getenv(secret_env, "").strip()
    api_pass = os.getenv(pass_env, "").strip()
    if not api_key or not api_secret:
        return None, f"Missing env vars {key_env} or {secret_env}"
    ex = ccxt.coinbasepro({
        "apiKey": api_key,
        "secret": api_secret,
        "password": api_pass,
        "enableRateLimit": True,
    })
    return ex, None

def safe_fetch_balance(exchange):
    try:
        bal = exchange.fetch_balance()
        totals = bal.get("total", {})
        if not totals:
            # sometimes ccxt returns different keys
            totals = {k: v for k, v in bal.items() if k not in ("info",)}
        return True, totals
    except Exception as e:
        return False, str(e)

def main():
    print("🔎 Nija Coinbase Connection Tester\n")

    # Spot
    spot, err = make_exchange("COINBASE_SPOT_KEY", "COINBASE_SPOT_SECRET", "COINBASE_SPOT_PASSPHRASE")
    if err:
        print("Spot: ❌", err)
    else:
        ok, res = safe_fetch_balance(spot)
        if ok:
            print("Spot: ✅ connection OK. Balances (non-zero shown):")
            for c, amt in res.items():
                if amt and float(amt) != 0.0:
                    print(f"  {c}: {amt}")
            print("  (If nothing printed above, you have zero balances.)")
        else:
            print("Spot: ❌ Error fetching balance:", res)

    print("\n---\n")

    # Futures
    fut, err = make_exchange("COINBASE_FUTURES_KEY", "COINBASE_FUTURES_SECRET", "COINBASE_FUTURES_PASSPHRASE")
    if err:
        print("Futures: ❌", err)
    else:
        ok, res = safe_fetch_balance(fut)
        if ok:
            print("Futures: ✅ connection OK. Balances (non-zero shown):")
            for c, amt in res.items():
                if amt and float(amt) != 0.0:
                    print(f"  {c}: {amt}")
            print("  (If nothing printed above, you have zero balances.)")
        else:
            print("Futures: ❌ Error fetching balance:", res)

    print("\nDone. If you see 'connection OK' for Spot or Futures, that key works.")
    print("If you see errors, re-check the key, secret, passphrase and permissions.")
    sys.exit(0)

if __name__ == "__main__":
    main()
