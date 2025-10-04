# main.py - Robust import-safe NIJA Trading Bot single-file entrypoint
import os
import sys
import importlib
import pkgutil
import traceback
import logging
from typing import Optional, Any, Dict
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

# optional numpy usage (don't crash if it's absent)
try:
    import numpy as np
except Exception:
    np = None

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("nija")

# ---------------- Coinbase client discovery (safe) ----------------
CLIENT_MODULE_NAMES = [
    "coinbase_advanced_py",
    "coinbase_advanced",
    "coinbase",
    "coinbase.wallet",
    "coinbase.wallet.client",
    "coinbase.client",
]

FOUND_CLIENT_MODULE: Optional[str] = None
FOUND_CLIENT_CLASS: Optional[Any] = None

def discover_coinbase_client():
    global FOUND_CLIENT_MODULE, FOUND_CLIENT_CLASS
    for name in CLIENT_MODULE_NAMES:
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        # inspect for common class names
        for attr in ("Client", "WalletClient", "CoinbaseClient", "AdvancedClient"):
            if hasattr(mod, attr):
                FOUND_CLIENT_MODULE = name
                FOUND_CLIENT_CLASS = getattr(mod, attr)
                log.info("Found Coinbase client class %s in module %s", attr, name)
                return
        # fallback: find a callable attribute that looks like a client
        for a in dir(mod):
            if a.startswith("_"):
                continue
            try:
                obj = getattr(mod, a)
            except Exception:
                continue
            if callable(obj) and ("client" in a.lower() or "coinbase" in a.lower() or "wallet" in a.lower()):
                FOUND_CLIENT_MODULE = name
                FOUND_CLIENT_CLASS = obj
                log.info("Found Coinbase-like callable %s in module %s", a, name)
                return
    # not found
    log.warning("No Coinbase client library discovered (tried: %s)", CLIENT_MODULE_NAMES)

discover_coinbase_client()

# helper to instantiate client safely (many libs accept different kw names)
def instantiate_client_from_env() -> Optional[Any]:
    """Try environment-based instantiation with obvious kw names."""
    if FOUND_CLIENT_CLASS is None:
        return None
    candidates = [
        {"api_key": os.getenv("COINBASE_API_KEY"), "api_secret": os.getenv("COINBASE_API_SECRET")},
        {"key": os.getenv("COINBASE_API_KEY"), "secret": os.getenv("COINBASE_API_SECRET")},
        {"API_KEY": os.getenv("COINBASE_API_KEY"), "API_SECRET": os.getenv("COINBASE_API_SECRET")},
        {},  # try no-arg
    ]
    last_exc = None
    for kw in candidates:
        kw_clean = {k:v for k,v in kw.items() if v}
        try:
            if kw_clean:
                inst = FOUND_CLIENT_CLASS(**kw_clean)
            else:
                inst = FOUND_CLIENT_CLASS()
            log.info("Instantiated client class %s with args %s", getattr(FOUND_CLIENT_CLASS, "__name__", str(FOUND_CLIENT_CLASS)), list(kw_clean.keys()))
            return inst
        except Exception as e:
            last_exc = e
            log.debug("Attempt to instantiate client with %s failed: %s", kw_clean, repr(e))
    log.warning("Failed to instantiate discovered client class; last error: %s", repr(last_exc))
    return None

# ---------------- FastAPI app ----------------
app = FastAPI(title="NIJA Trading Bot (safe loader)")

@app.get("/")
async def root():
    return {
        "status": "NIJA Trading Bot online",
        "coinbase_client_discovered": bool(FOUND_CLIENT_CLASS),
        "coinbase_module": FOUND_CLIENT_MODULE,
        "numpy_available": bool(np is not None),
        "python": sys.version,
    }

@app.get("/diag")
async def diag():
    # small diagnostic summary to help debugging on Render
    installed = []
    try:
        for _, name, _ in pkgutil.iter_modules():
            installed.append(name)
            if len(installed) >= 200:
                break
    except Exception as e:
        installed = ["error enumerating installed: " + repr(e)]
    return {
        "found_client_module": FOUND_CLIENT_MODULE,
        "found_client_class": getattr(FOUND_CLIENT_CLASS, "__name__", repr(FOUND_CLIENT_CLASS)) if FOUND_CLIENT_CLASS else None,
        "env": {k: ("REDACTED" if "KEY" in k or "SECRET" in k else v) for k,v in os.environ.items() if k.startswith("COINBASE") or k.startswith("WEBHOOK") or k.startswith("API")},
        "installed_sample": installed[:200],
    }

@app.get("/tryclient")
async def tryclient():
    """Try importing well-known names and return attributes (for debugging)."""
    out = {}
    for name in CLIENT_MODULE_NAMES:
        try:
            m = importlib.import_module(name)
            out[name] = {"imported": True, "attrs_sample": [a for a in dir(m) if not a.startswith("_")][:80]}
        except Exception as e:
            out[name] = {"imported": False, "error": repr(e)}
    out["_loader"] = {"found_client_module": FOUND_CLIENT_MODULE, "found_client_class": getattr(FOUND_CLIENT_CLASS, "__name__", None) if FOUND_CLIENT_CLASS else None}
    return out

# ---------------- Webhook and trade handling ----------------
class WebhookPayload(BaseModel):
    secret: Optional[str] = None
    symbol: Optional[str] = None
    action: Optional[str] = None
    # optional fields TradingView users often include
    price: Optional[float] = None
    size: Optional[float] = None
    extra: Optional[dict] = None

@app.post("/webhook")
async def webhook_listener(payload: WebhookPayload, request: Request):
    # TradingView webhook incoming
    webhook_secret = os.getenv("WEBHOOK_SECRET")
    if webhook_secret and payload.secret != webhook_secret:
        raise HTTPException(status_code=401, detail="Unauthorized webhook secret")
    symbol = payload.symbol
    action = (payload.action or "").lower()
    # minimal validation
    if not symbol or action not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="Invalid payload: need symbol and action 'buy' or 'sell'")
    # instantiate client lazily
    client = instantiate_client_from_env()
    if client is None:
        # do not crash — respond and log; you can still see debug endpoints
        log.error("Received webhook but no Coinbase client available. Payload: %s", payload.dict())
        return {"status": "no-client", "message": "No Coinbase client available to execute trade", "received": payload.dict()}
    # build a conservative payload for common client shapes
    size = payload.size or float(os.getenv("DEFAULT_SIZE", "0.001"))
    price = payload.price
    # Attempt to call typical methods on coinbase libs
    try:
        # Many libs have create_order(product_id=..., side=..., size=..., price=..., type='market')
        if hasattr(client, "create_order"):
            body = {"product_id": symbol, "side": action}
            if size:
                body["size"] = size
            if price:
                body["price"] = price
            try:
                res = client.create_order(**body)
            except TypeError:
                res = client.create_order(symbol, action, size, price)
            return {"status": "order_sent", "method": "create_order", "result": repr(res)[:2000]}
        # older clients may have client.orders.create()
        elif hasattr(client, "orders") and hasattr(client.orders, "create"):
            body = {"product_id": symbol, "side": action}
            if size:
                body["size"] = size
            if price:
                body["price"] = price
            res = client.orders.create(body)
            return {"status": "order_sent", "method": "client.orders.create", "result": repr(res)[:2000]}
        # final fallback: attempt a generic place_order if present
        elif hasattr(client, "place_order"):
            body = {"symbol": symbol, "side": action, "quantity": size}
            if price:
                body["price"] = price
            res = client.place_order(**body)
            return {"status": "order_sent", "method": "place_order", "result": repr(res)[:2000]}
        else:
            log.error("Client present but no known order method. Client repr: %s", repr(client)[:400])
            return {"status": "no_order_method", "message": "Client present but no known order method"}
    except Exception as e:
        tb = traceback.format_exc()
        log.error("Error while trying to send order: %s\n%s", repr(e), tb)
        return {"status": "error", "error": repr(e), "traceback": tb}

# simple manual trade endpoint for testing
class TradeReq(BaseModel):
    product: str
    side: str
    size: Optional[float] = None
    price: Optional[float] = None

@app.post("/trade")
async def trade(req: TradeReq):
    client = instantiate_client_from_env()
    if client is None:
        raise HTTPException(status_code=500, detail="No Coinbase client available")
    try:
        if hasattr(client, "create_order"):
            body = {"product_id": req.product, "side": req.side}
            if req.size:
                body["size"] = req.size
            if req.price:
                body["price"] = req.price
            try:
                res = client.create_order(**body)
            except TypeError:
                res = client.create_order(req.product, req.side, req.size, req.price)
            return {"ok": True, "method": "create_order", "result": repr(res)[:2000]}
        elif hasattr(client, "orders") and hasattr(client.orders, "create"):
            body = {"product_id": req.product, "side": req.side}
            if req.size:
                body["size"] = req.size
            if req.price:
                body["price"] = req.price
            res = client.orders.create(body)
            return {"ok": True, "method": "client.orders.create", "result": repr(res)[:2000]}
        elif hasattr(client, "place_order"):
            body = {"symbol": req.product, "side": req.side, "quantity": req.size}
            if req.price:
                body["price"] = req.price
            res = client.place_order(**body)
            return {"ok": True, "method": "place_order", "result": repr(res)[:2000]}
        else:
            raise RuntimeError("No known order method on discovered client.")
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": repr(e)})
