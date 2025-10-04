# main.py
# Single-file entrypoint: robust Coinbase loader + diagnostics + guarded trade endpoints

import os
import sys
import importlib
import importlib.util
import pkgutil
import platform
import traceback
import logging
from typing import Optional, Any, Tuple
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import numpy as np
from coinbase_advanced_py import Client
import os

c = Client(os.getenv("API_KEY"), os.getenv("API_SECRET"))

def adaptive_position_size(equity, volatility, risk=0.01):
    # Max 1% risk per trade
    size = equity * risk / volatility
    return max(0.001, size)  # Ensure minimum trade

def adaptive_tp(price, volatility, trend_strength):
    return price + trend_strength * volatility

def adaptive_sl(price, volatility, trend_strength):
    return price - trend_strength * volatility

def execute_trade(symbol, side, quantity, price, tp, sl):
    order = c.place_order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        type="market",
        take_profit=tp,
        stop_loss=sl
    )
    return order

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("coinbase_loader")

# ---------- Discovery globals ----------
CLIENT_CLASS: Optional[Any] = None
CLIENT_MODULE: Optional[str] = None
DISCOVERY = {"attempts": []}

PREFERRED_NAMES = ["Client", "WalletClient", "CoinbaseClient", "AdvancedClient"]

def looks_like_client_attr(obj_name: str, obj: Any) -> bool:
    if not callable(obj):
        return False
    lname = obj_name.lower()
    if obj_name in PREFERRED_NAMES:
        return True
    if "client" in lname or "wallet" in lname or "coinbase" in lname:
        return True
    return False

def inspect_module_for_client(mod) -> Tuple[Optional[Any], Optional[str]]:
    names = [n for n in dir(mod) if not n.startswith("_")]
    for p in PREFERRED_NAMES:
        if p in names:
            cand = getattr(mod, p)
            if callable(cand):
                return cand, p
    for n in names:
        try:
            obj = getattr(mod, n)
        except Exception:
            continue
        if looks_like_client_attr(n, obj):
            return obj, n
    return None, None

def try_import_by_name(name: str):
    info = {"name": name, "found": False, "spec": None, "attrs_sample": None, "error": None}
    try:
        spec = importlib.util.find_spec(name)
        info["spec"] = None if spec is None else {"name": spec.name, "origin": getattr(spec, "origin", None)}
        if spec is None:
            return info
        m = importlib.import_module(name)
        info["found"] = True
        info["attrs_sample"] = sorted([a for a in dir(m) if not a.startswith("_")])[:80]
    except Exception as e:
        info["error"] = repr(e)
    return info

def brute_force_discover():
    global CLIENT_CLASS, CLIENT_MODULE
    tried = []
    # allow forcing a module via env
    forced = os.getenv("FORCE_COINBASE_MODULE")
    seeds = [
        "coinbase_advanced_py",
        "coinbase_advanced",
        "coinbase",
        "coinbase.wallet",
        "coinbase.wallet.client",
        "coinbase.client",
    ]
    if forced:
        seeds.insert(0, forced)
    # try explicit seeds first
    for name in seeds:
        info = try_import_by_name(name)
        tried.append(info)
        if info.get("found"):
            try:
                m = importlib.import_module(name)
                cand, cand_name = inspect_module_for_client(m)
                if cand:
                    CLIENT_CLASS = cand
                    CLIENT_MODULE = f"{name}:{cand_name}"
                    return tried
            except Exception as e:
                tried[-1]["error"] = repr(e)
    # scan installed modules (pkgutil)
    scanned = []
    try:
        for finder, module_name, ispkg in pkgutil.iter_modules():
            if "coinbase" in module_name or "coinbase_advanced" in module_name:
                scanned.append(module_name)
    except Exception:
        # ignore
        pass

    for nm in scanned:
        info = try_import_by_name(nm)
        tried.append(info)
        if info.get("found"):
            try:
                m = importlib.import_module(nm)
                cand, cand_name = inspect_module_for_client(m)
                if cand:
                    CLIENT_CLASS = cand
                    CLIENT_MODULE = f"{nm}:{cand_name}"
                    return tried
                for sub in (f"{nm}.client", f"{nm}.wallet", f"{nm}.wallet.client"):
                    info2 = try_import_by_name(sub)
                    tried.append(info2)
                    if info2.get("found"):
                        try:
                            ms = importlib.import_module(sub)
                            cand, cand_name = inspect_module_for_client(ms)
                            if cand:
                                CLIENT_CLASS = cand
                                CLIENT_MODULE = f"{sub}:{cand_name}"
                                return tried
                        except Exception as e:
                            tried[-1]["error"] = repr(e)
            except Exception as e:
                tried[-1]["error"] = repr(e)
    return tried

DISCOVERY["attempts"] = brute_force_discover()
if CLIENT_CLASS:
    log.info("Discovered Coinbase client class %s from %s", getattr(CLIENT_CLASS, "__name__", str(CLIENT_CLASS)), CLIENT_MODULE)
else:
    log.warning("No Coinbase client discovered. Running in diagnostic mode.")

def instantiate_client_safe(**kwargs) -> Tuple[Optional[Any], dict]:
    info = {"attempts": [], "success": False}
    if CLIENT_CLASS is None:
        info["error"] = "No CLIENT_CLASS discovered"
        return None, info
    candidates = []
    if kwargs:
        candidates.append(kwargs)
    candidates.extend([
        {"api_key": kwargs.get("api_key") if kwargs else None, "api_secret": kwargs.get("api_secret") if kwargs else None},
        {"key": kwargs.get("key") if kwargs else None, "secret": kwargs.get("secret") if kwargs else None},
        {"api_key": os.getenv("COINBASE_API_KEY"), "api_secret": os.getenv("COINBASE_API_SECRET")},
        {},
    ])
    for c in candidates:
        cleaned = {k: v for k, v in (c or {}).items() if v is not None}
        attempt = {"kwargs": {k: ("REDACTED" if "key" in k.lower() or "secret" in k.lower() else v) for k, v in cleaned.items()}, "error": None}
        try:
            inst = CLIENT_CLASS(**cleaned) if cleaned else CLIENT_CLASS()
            attempt["instance_repr"] = repr(inst)[:400]
            info["attempts"].append(attempt)
            info["success"] = True
            return inst, info
        except Exception as e:
            attempt["error"] = repr(e)
            info["attempts"].append(attempt)
    return None, info

# ---------- FastAPI app ----------
app = FastAPI(title="NIJA Coinbase Diagnostic & Loader", version="1.0")

def installed_snapshot(limit=200):
    out = []
    try:
        for _, name, _ in pkgutil.iter_modules():
            out.append(name)
            if len(out) >= limit:
                break
    except Exception as e:
        return {"error": repr(e)}
    return out

@app.get("/")
async def root():
    return {"status": "ok", "client_found": bool(CLIENT_CLASS), "client_module": CLIENT_MODULE}

@app.get("/diag2")
async def diag2():
    try:
        site_paths = []
        try:
            import site
            site_paths = site.getsitepackages() if hasattr(site, "getsitepackages") else [site.getusersitepackages()]
        except Exception:
            site_paths = [p for p in sys.path if "site-packages" in p or "dist-packages" in p][:6]
        response = {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "platform": platform.platform(),
            "cwd": os.getcwd(),
            "sys_path_sample": sys.path[:80],
            "site_paths": site_paths,
            "discovery_summary": DISCOVERY,
            "client_found": bool(CLIENT_CLASS),
            "client_module": CLIENT_MODULE,
            "installed_sample": installed_snapshot(limit=400),
        }
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": repr(e), "traceback": traceback.format_exc()}, status_code=500)

@app.get("/tryclient")
async def tryclient():
    names = ["coinbase_advanced_py", "coinbase_advanced", "coinbase"]
    out = {}
    for n in names:
        try:
            m = importlib.import_module(n)
            out[n] = {"imported": True, "repr": repr(m)[:400], "attrs": sorted([a for a in dir(m) if not a.startswith("_")])[:80]}
        except Exception as e:
            out[n] = {"imported": False, "error": repr(e)}
    out["_loader"] = {"client_found": bool(CLIENT_CLASS), "client_module": CLIENT_MODULE, "discovery_attempts": DISCOVERY["attempts"]}
    return out

class InstReq(BaseModel):
    api_key: str | None = None
    api_secret: str | None = None
    key: str | None = None
    secret: str | None = None
    extra: dict | None = None

@app.post("/instantiate")
async def instantiate(req: InstReq):
    if CLIENT_CLASS is None:
        raise HTTPException(status_code=400, detail="No client discovered; check /diag2")
    kwargs = {}
    if req.api_key:
        kwargs["api_key"] = req.api_key
    if req.api_secret:
        kwargs["api_secret"] = req.api_secret
    if req.key:
        kwargs["key"] = req.key
    if req.secret:
        kwargs["secret"] = req.secret
    if req.extra:
        kwargs.update(req.extra)
    inst, info = instantiate_client_safe(**kwargs)
    return {"success": info.get("success", False), "attempts": info.get("attempts", []), "client_module": CLIENT_MODULE}

class TradeReq(BaseModel):
    side: str
    product: str
    size: float | None = None
    price: float | None = None
    test: bool | None = True

@app.post("/trade")
async def trade(req: TradeReq):
    if CLIENT_CLASS is None:
        raise HTTPException(status_code=400, detail="No client discovered; check /diag2 and /instantiate")
    api_key = os.getenv("COINBASE_API_KEY")
    api_secret = os.getenv("COINBASE_API_SECRET")
    if not api_key or not api_secret:
        raise HTTPException(status_code=400, detail="No API credentials found in environment (COINBASE_API_KEY / COINBASE_API_SECRET)")
    inst, info = instantiate_client_safe(api_key=api_key, api_secret=api_secret)
    if not info.get("success"):
        raise HTTPException(status_code=500, detail={"error": "Failed to instantiate client", "attempts": info.get("attempts")})
    client = inst
    result = {"called": None, "error": None, "result": None}
    try:
        if hasattr(client, "create_order"):
            result["called"] = "create_order"
            try:
                # Many client libs take different args; we're trying a common payload here.
                payload = {"product_id": req.product, "side": req.side}
                if req.size is not None:
                    payload["size"] = req.size
                if req.price is not None:
                    payload["price"] = req.price
                # if client's create_order signature is (product_id, side, size, price)
                try:
                    res = client.create_order(**payload)
                except TypeError:
                    # try positional
                    res = client.create_order(req.product, req.side, req.size, req.price)
                result["result"] = repr(res)[:2000]
            except Exception as e:
                result["error"] = repr(e)
        elif hasattr(client, "orders") and hasattr(client.orders, "create"):
            result["called"] = "client.orders.create"
            try:
                payload = {"product_id": req.product, "side": req.side}
                if req.size is not None:
                    payload["size"] = req.size
                if req.price is not None:
                    payload["price"] = req.price
                res = client.orders.create(payload)
                result["result"] = repr(res)[:2000]
            except Exception as e:
                result["error"] = repr(e)
        else:
            result["error"] = "No known order method on client; inspect client API and adapt."
    except Exception as e:
        result["error"] = repr(e)
    return result
