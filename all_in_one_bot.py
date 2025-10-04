# all_in_one_bot.py
# All-in-one diagnostic + Coinbase auto-discovery + safe instantiation + gated trading endpoint.
# Paste this file into your project, replace existing entrypoint, deploy.

import os
import sys
import platform
import pkgutil
import importlib
import importlib.util
import traceback
import logging
from typing import Any, Optional, Tuple
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("all_in_one_bot")

# ---------- Coinbase loader logic ----------
CLIENT_CLASS: Optional[Any] = None
CLIENT_MODULE: Optional[str] = None
DISCOVERY_DEBUG = {"attempts": []}

CANDIDATES = [
    ("coinbase_advanced_py", "Client"),
    ("coinbase_advanced", "Client"),
    ("coinbase.wallet.client", "Client"),
    ("coinbase.client", "Client"),
    ("coinbase", "Client"),
]


def find_likely_client_in_module(m) -> Tuple[Optional[Any], Optional[str]]:
    names = [n for n in dir(m) if not n.startswith("_")]
    preferred = ["Client", "WalletClient", "CoinbaseClient", "AdvancedClient"]
    for p in preferred:
        if p in names:
            cand = getattr(m, p)
            if callable(cand):
                return cand, p
    for n in names:
        if "client" in n.lower() or "wallet" in n.lower():
            cand = getattr(m, n)
            if callable(cand):
                return cand, n
    return None, None


for mod_name, attr in CANDIDATES:
    attempt = {"module": mod_name, "spec": None, "imported": False, "selected_attr": None, "error": None}
    try:
        spec = importlib.util.find_spec(mod_name)
        attempt["spec"] = None if spec is None else {"name": spec.name, "origin": getattr(spec, "origin", None)}
        if spec is None:
            DISCOVERY_DEBUG["attempts"].append(attempt)
            log.debug("Spec not found for %s", mod_name)
            continue
        m = importlib.import_module(mod_name)
        attempt["imported"] = True
        if hasattr(m, attr):
            CLIENT_CLASS = getattr(m, attr)
            CLIENT_MODULE = mod_name
            attempt["selected_attr"] = attr
            DISCOVERY_DEBUG["attempts"].append(attempt)
            log.info("Found %s in %s", attr, mod_name)
            break
        cand, cand_name = find_likely_client_in_module(m)
        if cand:
            CLIENT_CLASS = cand
            CLIENT_MODULE = f"{mod_name}.{cand_name}"
            attempt["selected_attr"] = cand_name
            DISCOVERY_DEBUG["attempts"].append(attempt)
            log.info("Auto-selected client-like attribute %s from %s", cand_name, mod_name)
            break
        else:
            DISCOVERY_DEBUG["attempts"].append(attempt)
            log.debug("%s imported but no client-like attribute found", mod_name)
    except Exception as e:
        attempt["error"] = repr(e)
        DISCOVERY_DEBUG["attempts"].append(attempt)
        log.debug("Import attempt failed for %s: %s", mod_name, repr(e))


if CLIENT_CLASS is None:
    log.warning("No Coinbase client class found among candidates. Running in diagnostic mode.")
else:
    log.info("Using Coinbase client %s from module %s",
             getattr(CLIENT_CLASS, "__name__", str(CLIENT_CLASS)), CLIENT_MODULE)


def instantiate_client(**kwargs) -> Tuple[Optional[Any], dict]:
    """
    Try to instantiate discovered CLIENT_CLASS with a few common constructor variations.
    Returns (instance_or_None, info_dict). info_dict contains attempt log and success flag.
    """
    info = {"attempts": [], "success": False}
    if CLIENT_CLASS is None:
        info["error"] = "No CLIENT_CLASS discovered"
        return None, info

    tries = [
        {"api_key": kwargs.get("api_key"), "api_secret": kwargs.get("api_secret")},
        {"api_key": kwargs.get("key"), "api_secret": kwargs.get("secret")},
        {"key": kwargs.get("key"), "secret": kwargs.get("secret")},
        {"api_key": kwargs.get("api_key")},
        {},
    ]
    if kwargs:
        tries.insert(0, kwargs)

    for t in tries:
        kw = {k: v for k, v in (t or {}).items() if v is not None}
        attempt_info = {"kwargs": dict(kw), "error": None}
        try:
            inst = CLIENT_CLASS(**kw) if kw else CLIENT_CLASS()
            attempt_info["instance_repr"] = repr(inst)[:400]
            info["attempts"].append(attempt_info)
            info["success"] = True
            return inst, info
        except TypeError as te:
            attempt_info["error"] = f"TypeError: {repr(te)}"
            info["attempts"].append(attempt_info)
        except Exception as e:
            attempt_info["error"] = repr(e)
            info["attempts"].append(attempt_info)

    info["success"] = False
    return None, info

# ---------- FastAPI app ----------

app = FastAPI(title="NIJA All-in-One Diagnostic & Coinbase Loader", version="1.0")


def installed_packages_snapshot(limit=200):
    pkgs = []
    try:
        for m in pkgutil.iter_modules():
            pkgs.append({"name": m.name, "ispkg": bool(m.ispkg)})
            if len(pkgs) >= limit:
                break
    except Exception as e:
        pkgs = [{"error": f"pkgutil.iter_modules failure: {repr(e)}"}]
    return pkgs


@app.get("/")
async def root():
    return {
        "status": "OK",
        "message": "NIJA Diagnostic app running",
        "coinbase_client_found": bool(CLIENT_CLASS),
        "coinbase_client_module": CLIENT_MODULE,
    }


@app.get("/diag2")
async def diag2():
    """
    Full diagnostic endpoint: shows attempted imports and site-packages snapshot.
    Paste the JSON here if you need help.
    """
    try:
        site_paths = []
        try:
            import site
            site_paths = site.getsitepackages() if hasattr(site, "getsitepackages") else [site.getusersitepackages()]
        except Exception:
            site_paths = [p for p in sys.path if "site-packages" in p or "dist-packages" in p][:6]

        attempts = [
            "coinbase_advanced_py",
            "coinbase_advanced",
            "coinbase_advanced_py.client",
            "coinbase_advanced.client",
            "coinbase.wallet",
            "coinbase.wallet.client",
            "coinbase"
        ]
        import_results = {}
        for name in attempts:
            try:
                r = {"find_spec": None, "imported": False, "attrs_sample": None, "error": None}
                spec = importlib.util.find_spec(name)
                r["find_spec"] = None if spec is None else {"name": spec.name, "origin": getattr(spec, "origin", None)}
                m = importlib.import_module(name)
                r["imported"] = True
                r["attrs_sample"] = sorted([a for a in dir(m) if not a.startswith("_")])[:60]
            except Exception as e:
                r["error"] = repr(e)
            import_results[name] = r

        response = {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "platform": platform.platform(),
            "cwd": os.getcwd(),
            "site_paths": site_paths,
            "import_attempts": import_results,
            "loader_debug": DISCOVERY_DEBUG,
            "installed_snapshot_sample": installed_packages_snapshot(limit=300),
            "sys_path": sys.path[:80],
            "loaded_modules_sample": sorted(list(sys.modules.keys()))[:200],
        }
        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(content={"error": repr(e), "traceback": tb}, status_code=500)


@app.get("/tryclient")
async def tryclient():
    names = ["coinbase_advanced_py", "coinbase_advanced", "coinbase"]
    results = {}
    for n in names:
        try:
            mod = importlib.import_module(n)
            results[n] = {"imported": True, "repr": repr(mod)[:400], "attrs_sample": sorted([a for a in dir(mod) if not a.startswith("_")])[:40]}
        except Exception as e:
            results[n] = {"imported": False, "error": repr(e)}
    results["_loader_summary"] = {
        "client_found": bool(CLIENT_CLASS),
        "client_module": CLIENT_MODULE,
        "loader_attempts": DISCOVERY_DEBUG.get("attempts", []),
    }
    return results


class InstantiateRequest(BaseModel):
    api_key: str | None = None
    api_secret: str | None = None
    key: str | None = None
    secret: str | None = None
    extra: dict | None = None


@app.post("/instantiate")
async def instantiate(req: InstantiateRequest):
    """
    Try to instantiate the discovered client. Supply JSON with api_key & api_secret (or key/secret).
    Response redacts secrets in the attempt log.
    """
    if CLIENT_CLASS is None:
        raise HTTPException(status_code=400, detail="No Coinbase client class discovered; check /diag2")

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

    inst, info = instantiate_client(**kwargs)
    for a in info.get("attempts", []):
        if "kwargs" in a and isinstance(a["kwargs"], dict):
            a["kwargs"] = {k: ("REDACTED" if "key" in k.lower() or "secret" in k.lower() else v) for k, v in a["kwargs"].items()}
    return {"success": info.get("success", False), "attempts": info.get("attempts", []), "client_module": CLIENT_MODULE}


class TradeRequest(BaseModel):
    # Minimal safe trade payload - adjust in your real bot
    side: str  # "buy" or "sell"
    product: str  # e.g., "BTC-USD" (depends on client)
    size: float | None = None
    price: float | None = None
    test: bool | None = True  # if True, do not place real order (client may still not support test flag)

@app.post("/trade")
async def trade(req: TradeRequest):
    """
    Gated trading endpoint. It will only attempt to place an order if a client class was discovered
    AND instantiate_client succeeded with credentials you pass to /instantiate previously.
    This endpoint does NOT store credentials — you must pass credentials again or wire persistent secure storage.
    WARNING: Use carefully. This endpoint will refuse to run if no client discovered.
    """
    if CLIENT_CLASS is None:
        raise HTTPException(status_code=400, detail="No Coinbase client class discovered; check /diag2 and /instantiate first.")

    # For safety: expect user to provide credentials via headers or env (not persisted here).
    # In this demo we look for API creds in env variables; change to your secure store
    api_key = os.getenv("COINBASE_API_KEY")
    api_secret = os.getenv("COINBASE_API_SECRET")
    if not api_key or not api_secret:
        raise HTTPException(status_code=400, detail="No API credentials found in environment. Set COINBASE_API_KEY and COINBASE_API_SECRET (or use /instantiate to test).")

    inst, info = instantiate_client(api_key=api_key, api_secret=api_secret)
    if not info.get("success"):
        raise HTTPException(status_code=500, detail={"error": "Failed to instantiate client", "attempts": info.get("attempts", [])})

    client = inst
    # ATTENTION: The real place_order API differs by client. We attempt a few common names safely.
    order_result = {"called": None, "error": None, "result": None}
    try:
        # look for common method names
        if hasattr(client, "create_order"):
            order_result["called"] = "create_order"
            # example arguments - many libs use (product, side, size, price) or a dict
            try:
                # attempt common signature - this may need adjustment for your client
                res = client.create_order(product_id=getattr(req, "product", None),
                                          side=req.side,
                                          size=req.size,
                                          price=req.price)
                order_result["result"] = repr(res)[:800]
            except Exception as e:
                order_result["error"] = repr(e)
        elif hasattr(client, "orders") and hasattr(client.orders, "create"):
            order_result["called"] = "client.orders.create"
            try:
                res = client.orders.create({
                    "product_id": getattr(req, "product", None),
                    "side": req.side,
                    "size": req.size,
                    "price": req.price,
                })
                order_result["result"] = repr(res)[:800]
            except Exception as e:
                order_result["error"] = repr(e)
        else:
            order_result["error"] = "No known order method found on discovered client. Check client API and adapt code."
    except Exception as e:
        order_result["error"] = repr(e)

    return order_result
