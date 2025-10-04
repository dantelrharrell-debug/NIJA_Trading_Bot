# all_in_one_bot.py
"""
All-in-one bot + diagnostic FastAPI app with robust Coinbase client discovery.
- Drop this into your repo (replace existing fragile imports).
- By default this runs in diagnostic (dry-run) mode.
- To enable live trading you MUST set environment variables:
    LIVE_TRADING=1
    COINBASE_API_KEY
    COINBASE_API_SECRET
    (and any passphrase/token your client requires)
- Carefully adapt order payloads to the discovered client's API before enabling LIVE_TRADING.
"""

import os
import sys
import logging
import importlib
import importlib.util
import traceback
from typing import Optional, Tuple, Any, Callable, Dict
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# ---- Logging ----
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
log = logging.getLogger("all_in_one_bot")

# ---- Coinbase client auto-discovery ----
CANDIDATE_MODULES = [
    ("coinbase_advanced_py", "Client"),
    ("coinbase_advanced", "Client"),
    ("coinbase.wallet.client", "Client"),
    ("coinbase.client", "Client"),
    ("coinbase", "Client"),
]

def _find_likely_client_in_module(module) -> Tuple[Optional[Callable], Optional[str]]:
    """Heuristically find a client-like callable in a module."""
    names = [n for n in dir(module) if not n.startswith("_")]
    preferred = ["Client", "WalletClient", "CoinbaseClient", "AdvancedClient"]
    for p in preferred:
        if p in names:
            cand = getattr(module, p)
            if callable(cand):
                return cand, p
    for n in names:
        if "client" in n.lower() or "wallet" in n.lower():
            cand = getattr(module, n)
            if callable(cand):
                return cand, n
    return None, None

def get_coinbase_client_class() -> Tuple[Optional[Callable], Optional[str], Dict[str, Any]]:
    """
    Try to find and return (client_class_or_factory, identifier, import_debug).
    import_debug contains per-module status for diagnostics.
    """
    debug = {}
    for mod_name, attr_name in CANDIDATE_MODULES:
        try:
            spec = importlib.util.find_spec(mod_name)
            if spec is None:
                debug[mod_name] = "spec_not_found"
                continue
            m = importlib.import_module(mod_name)
            # If module itself provided a top-level 'Client', prefer it.
            if hasattr(m, attr_name):
                cand = getattr(m, attr_name)
                if callable(cand):
                    debug[mod_name] = f"found_attr:{attr_name}"
                    return cand, f"{mod_name}.{attr_name}", debug
            cand, name = _find_likely_client_in_module(m)
            if cand:
                debug[mod_name] = f"auto_selected:{name}"
                return cand, f"{mod_name}.{name}", debug
            debug[mod_name] = "imported_no_client_attr"
        except Exception as e:
            debug[mod_name] = f"import_failed:{repr(e)}"
    return None, None, debug

def try_instantiate_client(ClientClass: Callable, credentials: Dict[str, Any]) -> Tuple[Optional[Any], Optional[Exception]]:
    """
    Try multiple instantiation patterns on client class.
    Returns (instance, error) where instance is None on failure and error is the exception.
    """
    try:
        # 1) Try keyword args
        try:
            inst = ClientClass(**credentials) if credentials else ClientClass()
            return inst, None
        except TypeError as e_kw:
            # 2) Try positional (api_key, api_secret)
            try:
                if "api_key" in credentials and "api_secret" in credentials:
                    inst = ClientClass(credentials["api_key"], credentials["api_secret"])
                    return inst, None
            except Exception:
                pass
            # 3) Try single token/env var style
            try:
                token = credentials.get("token") or credentials.get("COINBASE_TOKEN") or credentials.get("coinbase_token")
                if token:
                    inst = ClientClass(token)
                    return inst, None
            except Exception:
                pass
            # 4) Last resort, try parameterless
            try:
                inst = ClientClass()
                return inst, None
            except Exception:
                # Fall through
                pass
            return None, e_kw
    except Exception as e:
        return None, e

# ---- Collect credentials from env (do not print secrets) ----
def collect_credentials_from_env() -> Dict[str, Any]:
    creds = {}
    for k in ("COINBASE_API_KEY","COINBASE_API_SECRET","COINBASE_PASSPHRASE","COINBASE_TOKEN","API_KEY","API_SECRET"):
        if k in os.environ:
            creds[k.lower()] = os.environ[k]
    # also give common shorter keys
    if "coinbase_api_key" in os.environ:
        creds["api_key"] = os.environ["coinbase_api_key"]
    if "coinbase_api_secret" in os.environ:
        creds["api_secret"] = os.environ["coinbase_api_secret"]
    # allow override via a JSON blob env var (advanced)
    if "COINBASE_CREDS_JSON" in os.environ:
        import json
        try:
            creds.update(json.loads(os.environ["COINBASE_CREDS_JSON"]))
        except Exception:
            log.warning("Failed to parse COINBASE_CREDS_JSON")
    return creds

# Discover & instantiate if possible (but remain safe)
ClientClass, ClientIdentifier, discovery_debug = get_coinbase_client_class()
client_instance = None
client_inst_error = None
credentials = collect_credentials_from_env()
LIVE_TRADING = os.environ.get("LIVE_TRADING") in ("1", "true", "TRUE", "yes", "YES")

if ClientClass is None:
    log.warning("No Coinbase client class found. Discovery debug: %s", discovery_debug)
else:
    instance, err = try_instantiate_client(ClientClass, credentials)
    if instance:
        client_instance = instance
        log.info("Coinbase client instantiated from %s (LIVE_TRADING=%s)", ClientIdentifier, LIVE_TRADING)
    else:
        client_inst_error = err
        log.exception("Failed to instantiate Coinbase client %s: %s", ClientIdentifier, err)

# ---- FastAPI app ----
app = FastAPI(title="NIJA All-In-One Bot", version="1.0")

@app.get("/")
async def root():
    return {
        "status": "ok",
        "coinbase_client_available": bool(client_instance),
        "client_identifier": ClientIdentifier,
        "live_trading_enabled": bool(LIVE_TRADING),
    }

@app.get("/diag")
async def diag():
    # show diagnostics. Don't reveal secrets.
    safe_env = {
        "COINBASE_API_KEY_set": bool(os.environ.get("COINBASE_API_KEY") or os.environ.get("coinbase_api_key")),
        "COINBASE_API_SECRET_set": bool(os.environ.get("COINBASE_API_SECRET") or os.environ.get("coinbase_api_secret")),
        "COINBASE_TOKEN_set": bool(os.environ.get("COINBASE_TOKEN")),
        "LIVE_TRADING": bool(LIVE_TRADING),
    }
    return JSONResponse({
        "python": sys.version,
        "client_identifier": ClientIdentifier,
        "client_available": bool(client_instance),
        "client_inst_error": repr(client_inst_error) if client_inst_error else None,
        "discovery_debug": discovery_debug,
        "env": safe_env,
    })

# ---- Utility: safe order wrapper ----
def _client_has_method_names(obj, names):
    return any(hasattr(obj, n) for n in names)

def send_market_order(side: str, size: str = None, amount: str = None, product_id: str = "BTC-USD", price: Optional[str] = None) -> Dict[str, Any]:
    """
    Try multiple common client method signatures to place a market order.
    This is defensive and will return a dict describing what happened.
    You MUST adapt this to the discovered client API before using in production.
    """
    if client_instance is None:
        return {"success": False, "reason": "no_client"}

    # Don't do anything if not explicitly allowed
    if not LIVE_TRADING:
        return {"success": False, "reason": "dry_run", "message": "LIVE_TRADING not enabled. Set LIVE_TRADING=1 to enable."}

    try:
        # coinbase-advanced-py: client.create_order(product_id=..., side=..., type="market", size=...)
        if hasattr(client_instance, "create_order"):
            kwargs = {"product_id": product_id, "side": side, "type": "market"}
            if size:
                kwargs["size"] = size
            if amount:
                # some libraries use 'funds' or 'amount'
                kwargs["funds"] = amount
            if price:
                kwargs["price"] = price
            resp = client_instance.create_order(**kwargs)
            return {"success": True, "method": "create_order", "response": repr(resp)}
        # coinbase (old): client.buy/sell
        if side.lower() == "buy" and hasattr(client_instance, "buy"):
            kwargs = {}
            if amount:
                kwargs["amount"] = amount
                kwargs["currency"] = "USD"
            elif size:
                kwargs["amount"] = size
                kwargs["currency"] = "BTC"
            resp = client_instance.buy(**kwargs)
            return {"success": True, "method": "buy", "response": repr(resp)}
        if side.lower() == "sell" and hasattr(client_instance, "sell"):
            kwargs = {}
            if amount:
                kwargs["amount"] = amount
                kwargs["currency"] = "USD"
            elif size:
                kwargs["amount"] = size
                kwargs["currency"] = "BTC"
            resp = client_instance.sell(**kwargs)
            return {"success": True, "method": "sell", "response": repr(resp)}
        # generic fallback: try 'place_order', 'order', 'new_order'
        for candidate in ("place_order", "order", "new_order", "create_market_order"):
            if hasattr(client_instance, candidate):
                func = getattr(client_instance, candidate)
                try:
                    resp = func(side=side, size=size, product_id=product_id, amount=amount, price=price)
                    return {"success": True, "method": candidate, "response": repr(resp)}
                except TypeError:
                    # maybe different signature; try common minimal
                    try:
                        resp = func(product_id, side, size)
                        return {"success": True, "method": candidate, "response": repr(resp)}
                    except Exception:
                        pass
        return {"success": False, "reason": "unknown_client_api", "message": "Client present but no known order method found. Inspect client and adapt code."}
    except Exception as e:
        log.exception("Exception while attempting order")
        return {"success": False, "reason": "exception", "exception": repr(e), "traceback": traceback.format_exc()}

# ---- API endpoints for ordering ----
@app.post("/place_test_order")
async def place_test_order(request: Request):
    """
    Places a test order. Body can be JSON with: { "side": "buy"|"sell", "size":"0.001", "amount":"10", "product_id":"BTC-USD" }
    - By default this will NOT place a live order unless LIVE_TRADING=1 and API keys present.
    - This endpoint is only a convenience for diagnostics. Do not use it to run live aggressive trading without safeguards.
    """
    data = {}
    try:
        data = await request.json()
    except Exception:
        # ignore; maybe empty body -> use defaults
        pass

    side = str(data.get("side", "buy")).lower()
    size = data.get("size")
    amount = data.get("amount")
    product_id = data.get("product_id", "BTC-USD")
    price = data.get("price")

    # defensive sanity checks
    if side not in ("buy", "sell"):
        return JSONResponse({"error": "invalid_side", "allowed": ["buy", "sell"]}, status_code=400)

    # If there are no credentials yet and LIVE_TRADING requested, fail
    if LIVE_TRADING and not credentials:
        return JSONResponse({"error": "live_trading_requested_but_no_credentials_found"}, status_code=400)

    result = send_market_order(side=side, size=size, amount=amount, product_id=product_id, price=price)
    return JSONResponse(result)

@app.get("/client_methods")
async def client_methods():
    """Return a sample of callable attribute names on the discovered client (for debugging)."""
    if client_instance is None:
        return JSONResponse({"client": None})
    names = [n for n in dir(client_instance) if not n.startswith("_")]
    callables = [n for n in names if callable(getattr(client_instance, n, None))]
    # Return a slice so output stays small
    return JSONResponse({"client_identifier": ClientIdentifier, "callable_sample": callables[:80]})

# ---- Shutdown/startup events to log state ----
@app.on_event("startup")
async def on_startup():
    log.info("App startup. client_available=%s, client_identifier=%s, LIVE_TRADING=%s",
             bool(client_instance), ClientIdentifier, LIVE_TRADING)

@app.on_event("shutdown")
async def on_shutdown():
    log.info("App shutdown.")

# ---- If you run directly (for local dev) ----
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("all_in_one_bot:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), reload=False)
