# main.py
"""
NIJA Trading Bot single-file app
- robust Coinbase client discovery & diagnostics
- adaptive position sizing and TP/SL helpers
- endpoints: /, /diag2, /tryclient, /instantiate, /trade, /webhook
"""

import os
import sys
import pkgutil
import importlib
import importlib.util
import traceback
import platform
import logging
from typing import Optional, Any, Tuple, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# optional numpy: import if available, otherwise fallback to math
try:
    import numpy as np
except Exception:
    np = None
    import math

LOG = logging.getLogger("nija")
logging.basicConfig(level=logging.INFO)

# ---------- discovery globals ----------
CLIENT_CLASS: Optional[Any] = None
CLIENT_MODULE: Optional[str] = None
DISCOVERY: Dict[str, Any] = {"attempts": []}

# preferred candidate names to look for inside modules
PREFERRED_NAMES = ["Client", "WalletClient", "CoinbaseClient", "AdvancedClient", "ClientV2"]


def looks_like_client_attr(obj_name: str, obj: Any) -> bool:
    """Heuristic to decide if attr looks like a client constructor/class."""
    if not callable(obj):
        return False
    lname = obj_name.lower()
    if obj_name in PREFERRED_NAMES:
        return True
    if "client" in lname or "wallet" in lname or "coinbase" in lname or "advanced" in lname:
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
        info["attrs_sample"] = sorted([a for a in dir(m) if not a.startswith("_")])[:200]
    except Exception as e:
        info["error"] = repr(e)
    return info


def brute_force_discover():
    """Try common module names, then scan installed modules for coinbase-ish names."""
    global CLIENT_CLASS, CLIENT_MODULE
    tried = []
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
        # allow forced module:class format too
        if ":" in forced:
            mod_name, cls_name = forced.split(":", 1)
            info = try_import_by_name(mod_name)
            tried.append(info)
            if info.get("found"):
                try:
                    m = importlib.import_module(mod_name)
                    if hasattr(m, cls_name):
                        CLIENT_CLASS = getattr(m, cls_name)
                        CLIENT_MODULE = f"{mod_name}:{cls_name}"
                        return tried
                except Exception as e:
                    tried[-1]["error"] = repr(e)
        else:
            seeds.insert(0, forced)
    # try explicit seeds
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
    # scan installed modules
    scanned = []
    try:
        for finder, module_name, ispkg in pkgutil.iter_modules():
            if "coinbase" in module_name or "coinbase_advanced" in module_name:
                scanned.append(module_name)
    except Exception:
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


# run discovery now (will not raise if nothing found)
DISCOVERY["attempts"] = brute_force_discover()
if CLIENT_CLASS:
    LOG.info("Discovered Coinbase client class %s from %s", getattr(CLIENT_CLASS, "__name__", str(CLIENT_CLASS)), CLIENT_MODULE)
else:
    LOG.warning("No Coinbase client library discovered (tried: %s)", ["coinbase_advanced_py", "coinbase_advanced", "coinbase", "coinbase.wallet", "coinbase.wallet.client", "coinbase.client"])


def instantiate_client_safe(**kwargs) -> Tuple[Optional[Any], dict]:
    """
    Safe attempt to instantiate discovered CLIENT_CLASS with multiple common kwarg keys.
    Returns (instance_or_none, info_dict)
    """
    info = {"attempts": [], "success": False}
    if CLIENT_CLASS is None:
        info["error"] = "No CLIENT_CLASS discovered"
        return None, info
    candidates = []
    # provided kwargs first
    if kwargs:
        candidates.append(kwargs)
    # common key sets
    candidates.extend([
        {"api_key": kwargs.get("api_key") if kwargs else None, "api_secret": kwargs.get("api_secret") if kwargs else None},
        {"key": kwargs.get("key") if kwargs else None, "secret": kwargs.get("secret") if kwargs else None},
        {"api_key": os.getenv("COINBASE_API_KEY"), "api_secret": os.getenv("COINBASE_API_SECRET")},
        {"api_key": os.getenv("API_KEY"), "api_secret": os.getenv("API_SECRET")},
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


# ---------- Adaptive trading helpers ----------
def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


def volatility_from_prices(price_series):
    """
    Simple volatility estimator: use std dev of returns.
    Accepts numpy array or list.
    """
    try:
        if np is not None:
            arr = np.array(price_series, dtype=float)
            if arr.size < 2:
                return 1.0
            returns = np.diff(np.log(arr + 1e-12))
            vol = float(np.std(returns))
            return max(1e-6, vol)
        else:
            # fallback: rough estimate with math
            if not price_series or len(price_series) < 2:
                return 1.0
            import statistics
            returns = []
            for i in range(1, len(price_series)):
                prev = price_series[i - 1]
                cur = price_series[i]
                if prev:
                    returns.append(math.log((cur + 1e-12) / (prev + 1e-12)))
            if not returns:
                return 1.0
            return max(1e-6, statistics.pstdev(returns))
    except Exception:
        return 1.0


def adaptive_position_size(equity, volatility, risk=0.01):
    """Return position size in units (very simple): risk fraction of equity divided by volatility."""
    try:
        equity = float(equity)
        volatility = float(volatility) if volatility and volatility > 0 else 1.0
        size = equity * risk / volatility
        # clamp to a minimum and reasonable max
        size = max(size, 0.0001 * max(1.0, equity))
        size = min(size, equity)  # can't exceed equity
        return float(size)
    except Exception:
        return float(max(0.0001, 1.0))


def adaptive_tp(price, volatility, trend_strength=1.0):
    """Return take-profit price (price + k * volatility)."""
    try:
        return float(price) + float(trend_strength) * float(volatility)
    except Exception:
        return float(price)


def adaptive_sl(price, volatility, trend_strength=1.0):
    """Return stop-loss price (price - k * volatility)."""
    try:
        return float(price) - float(trend_strength) * float(volatility)
    except Exception:
        return float(price)


# ---------- FastAPI app ----------
app = FastAPI(title="NIJA Trading Bot", version="1.0")


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
    return {"status": "NIJA Trading Bot Online", "client_found": bool(CLIENT_CLASS), "client_module": CLIENT_MODULE}


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
    names = ["coinbase_advanced_py", "coinbase_advanced", "coinbase", "coinbase.wallet", "coinbase.wallet.client", "coinbase.client"]
    out = {}
    for n in names:
        try:
            m = importlib.import_module(n)
            out[n] = {"imported": True, "repr": repr(m)[:400], "attrs": sorted([a for a in dir(m) if not a.startswith("_")])[:200]}
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
        raise HTTPException(status_code=400, detail="No client discovered; check /diag2 or call /tryclient")
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
    # optional: historical price series for volatility calc
    price_series: list | None = None
    equity: float | None = None
    trend_strength: float | None = 1.0


@app.post("/trade")
async def trade(req: TradeReq):
    """Attempt to place an order using discovered/instantiated client. Returns diagnostic info."""
    if CLIENT_CLASS is None:
        raise HTTPException(status_code=400, detail="No client discovered; check /diag2 and /tryclient")
    # prefer env creds
    api_key = os.getenv("COINBASE_API_KEY") or os.getenv("API_KEY")
    api_secret = os.getenv("COINBASE_API_SECRET") or os.getenv("API_SECRET")
    if not api_key or not api_secret:
        # we still allow instantiate endpoint with explicit creds
        return {"error": "Missing API credentials in environment (COINBASE_API_KEY / COINBASE_API_SECRET)"}
    inst, info = instantiate_client_safe(api_key=api_key, api_secret=api_secret)
    if not info.get("success"):
        return {"error": "Failed to instantiate client", "attempts": info.get("attempts")}
    client = inst
    # compute volatility
    vol = 1.0
    if req.price_series:
        vol = volatility_from_prices(req.price_series)
    # compute adaptive size if not provided and equity provided
    size = req.size
    if size is None and req.equity:
        size = adaptive_position_size(req.equity, vol)
    result = {"called": None, "error": None, "result": None, "diagnostics": {"volatility": vol, "size": size}}
    try:
        # try client.create_order
        if hasattr(client, "create_order"):
            result["called"] = "create_order"
            try:
                payload = {"product_id": req.product, "side": req.side}
                if size is not None:
                    payload["size"] = size
                if req.price is not None:
                    payload["price"] = req.price
                try:
                    res = client.create_order(**payload)
                except TypeError:
                    res = client.create_order(req.product, req.side, size, req.price)
                result["result"] = repr(res)[:3000]
            except Exception as e:
                result["error"] = repr(e)
        # try client.orders.create
        elif hasattr(client, "orders") and hasattr(client.orders, "create"):
            result["called"] = "client.orders.create"
            try:
                payload = {"product_id": req.product, "side": req.side}
                if size is not None:
                    payload["size"] = size
                if req.price is not None:
                    payload["price"] = req.price
                res = client.orders.create(payload)
                result["result"] = repr(res)[:3000]
            except Exception as e:
                result["error"] = repr(e)
        # try place_order common call
        elif hasattr(client, "place_order"):
            result["called"] = "place_order"
            try:
                payload = {"symbol": req.product, "side": req.side, "quantity": size or 0, "price": req.price or 0, "type": "market"}
                res = client.place_order(**payload)
                result["result"] = repr(res)[:3000]
            except Exception as e:
                result["error"] = repr(e)
        else:
            result["error"] = "No known order method on client; inspect /tryclient attributes and adapt."
    except Exception as e:
        result["error"] = repr(e)
    return result


# minimal webhook support for TradingView
class WebhookReq(BaseModel):
    symbol: str | None = None
    action: str | None = None  # buy or sell
    price: float | None = None
    account_equity: float | None = None
    price_series: list | None = None
    secret: str | None = None


@app.post("/webhook")
async def webhook_listener(req: WebhookReq, request: Request):
    """Receive TradingView webhook signals. Expects JSON body containing at least symbol and action and secret."""
    data = await request.json()
    secret = data.get("secret")
    if os.getenv("WEBHOOK_SECRET"):
        if secret != os.getenv("WEBHOOK_SECRET"):
            LOG.warning("Webhook unauthorized attempt: secret mismatch")
            raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        LOG.warning("WEBHOOK_SECRET not set - accepting any incoming webhook (insecure)")

    symbol = data.get("symbol") or req.symbol
    action = data.get("action") or req.action
    price = data.get("price") or req.price
    equity = data.get("account_equity") or req.account_equity
    price_series = data.get("price_series") or req.price_series
    LOG.info("Webhook received: %s action=%s price=%s equity=%s", symbol, action, price, equity)

    # compute volatility & sizes
    vol = volatility_from_prices(price_series) if price_series else 1.0
    size = None
    if equity:
        size = adaptive_position_size(equity, vol)
    tp = adaptive_tp(price or 0.0, vol, trend_strength=1.0)
    sl = adaptive_sl(price or 0.0, vol, trend_strength=1.0)

    # Build a trade request body (but don't automatically send unless client available)
    trade_payload = {
        "symbol": symbol,
        "side": action,
        "quantity": size,
        "price": price,
        "type": "market",
        "take_profit": tp,
        "stop_loss": sl,
    }

    # attempt to place trade if client available & creds present
    trade_result = {"attempted": False, "details": None}
    if CLIENT_CLASS and (os.getenv("COINBASE_API_KEY") or os.getenv("API_KEY")):
        api_key = os.getenv("COINBASE_API_KEY") or os.getenv("API_KEY")
        api_secret = os.getenv("COINBASE_API_SECRET") or os.getenv("API_SECRET")
        inst, info = instantiate_client_safe(api_key=api_key, api_secret=api_secret)
        if info.get("success") and inst:
            client = inst
            trade_result["attempted"] = True
            try:
                # try sensible APIs
                if hasattr(client, "place_order"):
                    res = client.place_order(symbol=symbol, side=action, quantity=size, price=price, type="market", take_profit=tp, stop_loss=sl)
                    trade_result["details"] = repr(res)[:3000]
                elif hasattr(client, "create_order"):
                    payload = {"product_id": symbol, "side": action, "size": size, "price": price}
                    try:
                        res = client.create_order(**payload)
                    except TypeError:
                        res = client.create_order(symbol, action, size, price)
                    trade_result["details"] = repr(res)[:3000]
                elif hasattr(client, "orders") and hasattr(client.orders, "create"):
                    payload = {"product_id": symbol, "side": action, "size": size, "price": price}
                    res = client.orders.create(payload)
                    trade_result["details"] = repr(res)[:3000]
                else:
                    trade_result["details"] = "No known order API on client instance."
            except Exception as e:
                trade_result["details"] = "Order attempt error: " + repr(e)
        else:
            trade_result["details"] = {"instantiate_info": info}
    else:
        trade_result["details"] = "No client or credentials available; webhook processed in diagnostic mode."

    return {"status": "received", "trade_payload": trade_payload, "trade_result": trade_result}


# ---------- fallback explicit importer (helpful if client present but discovery missed) ----------
# This will run at import time and try to pick an explicit candidate if CLIENT_CLASS is None
if CLIENT_CLASS is None:
    try:
        explicit_names = [
            "coinbase_advanced_py",
            "coinbase_advanced_py.client",
            "coinbase_advanced.client",
            "coinbase.client",
            "coinbase",
        ]
        for en in explicit_names:
            try:
                m = importlib.import_module(en)
            except Exception:
                continue
            # check candidate class names
            found = False
            for cand in ("Client", "AdvancedClient", "CoinbaseClient", "WalletClient", "ClientV2"):
                if hasattr(m, cand):
                    CLIENT_CLASS = getattr(m, cand)
                    CLIENT_MODULE = f"{en}:{cand}"
                    LOG.info("Fallback found client class %s in %s", cand, en)
                    found = True
                    break
            if found:
                break
            # otherwise find first callable that looks like a client
            for a in dir(m):
                if a.startswith("_"):
                    continue
                try:
                    obj = getattr(m, a)
                except Exception:
                    continue
                if callable(obj) and ("client" in a.lower() or "coinbase" in a.lower()):
                    CLIENT_CLASS = obj
                    CLIENT_MODULE = f"{en}:{a}"
                    LOG.info("Fallback using attribute %s from %s", a, en)
                    found = True
                    break
            if found:
                break
    except Exception as e:
        LOG.debug("Fallback explicit importer error: %s", repr(e))
