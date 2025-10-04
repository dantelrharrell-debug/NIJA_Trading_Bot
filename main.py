# main.py
"""
Diagnostic FastAPI app that integrates coinbase_loader.
- GET /            -> simple status
- GET /diag2       -> full diagnostic JSON (site-packages, imports attempts)
- GET /tryclient   -> quick test of top-level coinbase modules import
- POST /instantiate-> attempt to instantiate discovered client (pass JSON with api_key, api_secret, etc.)
"""

import os
import sys
import platform
import pkgutil
import importlib
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("main")

# import our loader
import coinbase_loader

app = FastAPI(title="NIJA Diagnostic", version="1.0")


def installed_packages_snapshot(limit=300):
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
        "message": "NIJA Diagnostic running",
        "coinbase_client_found": bool(coinbase_loader.CLIENT_CLASS),
        "coinbase_client_module": coinbase_loader.CLIENT_MODULE,
    }


@app.get("/diag2")
async def diag2():
    try:
        # site-packages paths
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
            "loader_debug": coinbase_loader.DISCOVERY_DEBUG,
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
    # include loader summary
    results["_loader_summary"] = {
        "client_found": bool(coinbase_loader.CLIENT_CLASS),
        "client_module": coinbase_loader.CLIENT_MODULE,
        "loader_attempts": coinbase_loader.DISCOVERY_DEBUG.get("attempts", []),
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
    Attempt to instantiate discovered client. Supply JSON body with api_key & api_secret (or key/secret).
    Returns attempt log and a success boolean; does NOT print secrets back.
    """
    if coinbase_loader.CLIENT_CLASS is None:
        raise HTTPException(status_code=400, detail="No Coinbase client class discovered; check /diag2")

    # only pass required fields; don't echo secrets in the response
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

    inst, info = coinbase_loader.instantiate_client(**kwargs)
    # don't include secret values in returned info - redact obvious keys
    for a in info.get("attempts", []):
        if "kwargs" in a and isinstance(a["kwargs"], dict):
            a["kwargs"] = {k: ("REDACTED" if "key" in k.lower() or "secret" in k.lower() else v) for k, v in a["kwargs"].items()}

    return {"success": info.get("success", False), "attempts": info.get("attempts", []), "client_module": coinbase_loader.CLIENT_MODULE}
