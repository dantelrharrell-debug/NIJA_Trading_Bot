import os
import time
import requests

# Optional: enable dry run to prevent real trades
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")

# Public price fallback
COINBASE_SPOT_URL = "https://api.coinbase.com/v2/prices/{symbol}-USD/spot"

# -------------------------
# Helper: robust account lookup
# -------------------------
def _try_float(x):
    try:
        return float(x)
    except Exception:
        return None

def robust_get_account_balance(client, currency_code):
    """
    Try multiple ways to get the balance for a currency.
    currency_code: "USD", "BTC", "ETH", etc.
    Returns dict: {"amount": float, "currency": "USD"} or None on failure.
    """
    # 1) If using coinbase_advanced_py (older flows) it might have get_account_balance()
    try:
        if hasattr(client, "get_account_balance"):
            # some clients expect "USD" or "BTC"
            val = client.get_account_balance(currency_code)
            amt = _try_float(val)
            if amt is not None:
                return {"amount": amt, "currency": currency_code}
    except Exception as e:
        print(f"[robust_get] client.get_account_balance({currency_code}) failed: {e}")

    # 2) Try client.get_account(currency_code) — some SDKs accept currency param (but often expect an id)
    try:
        if hasattr(client, "get_account"):
            acct = client.get_account(currency_code)
            # acct might be an object with .balance.amount or .balance or a dict
            # handle many shapes
            if acct is None:
                raise ValueError("get_account returned None")
            # try attribute access
            try:
                bal = getattr(acct, "balance", None)
                if bal is not None:
                    # balance may be an object with .amount or a simple string
                    amt = None
                    if hasattr(bal, "amount"):
                        amt = _try_float(bal.amount)
                    else:
                        amt = _try_float(bal)
                    if amt is not None:
                        # currency maybe at acct.currency or bal.currency
                        cur = getattr(acct, "currency", None) or getattr(bal, "currency", None) or currency_code
                        return {"amount": amt, "currency": cur}
            except Exception:
                pass
            # try dict-like access
            try:
                # some SDKs return dicts
                if isinstance(acct, dict):
                    bal = acct.get("balance") or acct.get("available") or acct.get("amount")
                    if isinstance(bal, dict) and "amount" in bal:
                        amt = _try_float(bal["amount"])
                    else:
                        amt = _try_float(bal)
                    cur = acct.get("currency") or currency_code
                    if amt is not None:
                        return {"amount": amt, "currency": cur}
            except Exception:
                pass
    except Exception as e:
        print(f"[robust_get] client.get_account({currency_code}) failed: {e}")

    # 3) Try iterating over list of accounts (common pattern)
    try:
        if hasattr(client, "get_accounts"):
            all_accts = client.get_accounts()
            # all_accts may be list-like or an iterator
            try:
                for acct in all_accts:
                    # normalize dict/object
                    cur = None
                    bal_amt = None
                    if isinstance(acct, dict):
                        cur = acct.get("currency") or acct.get("balance", {}).get("currency")
                        bal = acct.get("balance") or acct.get("available") or {}
                        if isinstance(bal, dict):
                            bal_amt = _try_float(bal.get("amount") or bal.get("value"))
                        else:
                            bal_amt = _try_float(bal)
                    else:
                        # object with attributes
                        cur = getattr(acct, "currency", None)
                        bal = getattr(acct, "balance", None)
                        if bal is not None:
                            if hasattr(bal, "amount"):
                                bal_amt = _try_float(bal.amount)
                            else:
                                bal_amt = _try_float(bal)
                    if cur and cur.upper() == currency_code.upper():
                        if bal_amt is not None:
                            return {"amount": bal_amt, "currency": cur}
            except Exception as e:
                # sometimes get_accounts returns a paginated object; print debug
                print(f"[robust_get] iterating get_accounts failed: {e}")
    except Exception as e:
        print(f"[robust_get] client.get_accounts() failed: {e}")

    # 4) Nothing worked
    print(f"[robust_get] Failed to fetch account for {currency_code} via available client methods.")
    return None

# -------------------------
# Replace get_current_balance and get_coin_balance with robust versions
# -------------------------
def get_current_balance():
    """
    Returns USD float balance or None on failure.
    """
    try:
        res = robust_get_account_balance(client, "USD")
        if res and res.get("amount") is not None:
            return res["amount"]
        # If API returned 0 or None, print helpful debug
        print("Error fetching USD balance: No usable USD account returned.")
        return None
    except Exception as e:
        print(f"Error fetching USD balance: {e}")
        return None

def get_coin_balance(coin):
    """
    coin: 'BTC', 'ETH', ...
    Returns token amount (float) or None on failure.
    """
    try:
        res = robust_get_account_balance(client, coin)
        if res and res.get("amount") is not None:
            return res["amount"]
        print(f"[get_coin_balance] No usable account for {coin}")
        return None
    except Exception as e:
        print(f"[get_coin_balance] Error: {e}")
        return None

# -------------------------
# Robust USD value (price) lookup with SDK then public fallback
# -------------------------
def get_usd_value(coin, token_amount):
    """
    Returns USD equivalent or None.
    """
    # 1) Try SDK spot price if available
    try:
        if hasattr(client, "get_spot_price"):
            try:
                spot = client.get_spot_price(currency_pair=f"{coin}-USD")
                # spot might be object with .amount or dict
                if spot is None:
                    raise ValueError("spot returned None")
                price = None
                if hasattr(spot, "amount"):
                    price = _try_float(spot.amount)
                elif isinstance(spot, dict):
                    price = _try_float(spot.get("amount") or (spot.get("data") or {}).get("amount"))
                else:
                    # maybe string
                    price = _try_float(spot)
                if price is not None:
                    return token_amount * price
            except Exception as e:
                print(f"[price/sdk] get_spot_price failed for {coin}: {e}")
    except Exception:
        pass

    # 2) Fallback to public Coinbase API
    try:
        url = COINBASE_SPOT_URL.format(symbol=coin)
        r = requests.get(url, timeout=6)
        r.raise_for_status()
        j = r.json()
        amt = j.get("data", {}).get("amount")
        price = _try_float(amt)
        if price is not None:
            return token_amount * price
        else:
            print(f"[price/http] Coinbase public API returned bad payload for {coin}: {j}")
    except Exception as e:
        print(f"[price/http] Failed to fetch spot price for {coin}: {e}")

    # All attempts failed
    return None

# -------------------------
# Safe execute_trade with dry-run
# -------------------------
def execute_trade(asset, side="buy"):
    """
    Use DRY_RUN env flag to prevent real orders while debugging.
    asset example: 'BTC-USD'
    """
    # Determine trade amount using your allocate_dynamic function
    dynamic_allocations = allocate_dynamic(lambda: get_current_balance() or 0, coinbase_min, priority_order)
    trade_amount = dynamic_allocations.get(asset, 0)

    if trade_amount <= 0:
        print(f"Skipped {asset}: allocation below minimum or zero ({trade_amount}).")
        return False

    # Dry run only logs what would be done
    if DRY_RUN:
        print(f"[DRY RUN] Would place {side} market order for {asset} amount ${trade_amount:.2f}")
        return True

    # Real trade path (original)
    try:
        order = client.place_order(
            product_id=asset,
            side=side,
            order_type="market",
            size=str(trade_amount)
        )
        print(f"✅ Placed {side} order for {asset} with amount ${trade_amount}")
        return True
    except Exception as e:
        print(f"❌ Error placing order for {asset}: {e}")
        return False
