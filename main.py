# main.py - NIJA Trading Bot Diagnostic + Robust Coinbase Client Loader

import sys
import os
import platform
import importlib
import importlib.util
import pkgutil
import traceback
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("all_in_one_bot")

# -----------------------------
# Robust Coinbase client loader
# -----------------------------
CLIENT_CLASS = None
CLIENT_MODULE = None

candidates = [
    ("coinbase_advanced_py", "Client"),
    ("coinbase_advanced", "Client"),
    ("coinbase.wallet.client", "Client"),
    ("coinbase.client", "Client"),
    ("coinbase", "Client"),
]

def find_likely_client_in_module(m):
    """Return an attribute (callable/class) from module m that looks like a client."""
    names = [n for n in dir(m) if not n.startswith("_")]
    # prefer exact 'Client' or 'WalletClient'
    preferred = ["Client", "WalletClient", "CoinbaseClient", "AdvancedClient"]
    for p in preferred:
        if p in names:
            cand = getattr(m, p)
            if callable(cand):
                return cand, p
    # fallback: any name containing 'client' or 'Client'
    for n in names:
        if "client" in n.lower() or "wallet" in n.lower():
            cand = getattr(m, n)
            if callable(cand):
                return cand, n
    return None, None

for mod_name, attr in candidates:
    try:
        spec = importlib.util.find_spec(mod_name)
        if spec is None:
            log.debug("spec not found for %s", mod_name)
            continue
        m = importlib.import_module(mod_name)
        # If exact attr available, prefer it
        if hasattr(m, attr):
            CLIENT_CLASS = getattr(m, attr)
            CLIENT_MODULE = mod_name
            log.info("Found %s in %s", attr, mod_name)
            break
        # Otherwise attempt to find a likely class/function
        cand, cand_name = find_likely_client_in_module(m)
        if cand:
            CLIENT_CLASS = cand
            CLIENT_MODULE = mod_name + "." + cand_name
            log.info("Auto-selected client-like attribute %s from %s", cand_name, mod_name)
            break
        else:
            log.debug("%s imported but no candidate client attr found", mod_name)
    except Exception as e:
        log.debug("Import attempt failed for %s: %s", mod_name, repr(e))

if CLIENT_CLASS is None:
    log.warning("No Coinbase client class found among candidates. Running in diagnostic mode.")
else:
    log.info("Using Coinbase client %s from module %s",
             getattr(CLIENT_CLASS, "__name__", str(CLIENT_CLASS)), CLIENT_MODULE)

# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="NIJA Diagnostic", version="1.0")

def try_import(name):
    """Try to import a module by name, return dict with status and details."""
    out = {"name": name, "found": False, "import_error": None, "attrs": None}
    try:
        spec = importlib.util.find_spec(name)
        out["find_spec"] = None if spec is None else {"name": spec.name, "origin": getattr(spec, "origin", None)}
        module = importlib.import_module(name)
        out["found"] = True
        out["attrs"] = sorted([a for a in dir(module) if not a.startswith("_")])[:40]
    except Exception as e:
        out["import_error"] = repr(e)
    return out

def installed_packages_snapshot(limit=200):
    """Return list of installed packages from pkgutil and sys.modules sampling."""
    pkgs = []
    try:
        for m in pkgutil.iter_modules():
            pkgs.append({"name": m.name, "ispkg": bool(m.ispkg), "module_finder": type(m.module_finder).__name__})
            if len(pkgs) >= limit:
                break
    except Exception as e:
        pkgs = [{"error": f"pkgutil.iter_modules failure: {repr(e)}"}]
    return pkgs

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/")
async def root():
    return {"status": "OK", "message": "Diagnostic app running", "python": sys.version, "platform": platform.platform()}

@app.get("/modules")
async def modules():
    top_loaded = sorted(list(sys.modules.keys()))[:200]
    return {"python_version": sys.version, "top_loaded_modules_count": len(sys.modules), "top_loaded_sample": top_loaded}

@app.get("/diag2")
async def diag2():
    """Full diagnostic endpoint showing coinbase import attempts and environment."""
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
        import_results = {name: try_import(name) for name in attempts}
        installed_snapshot = installed_packages_snapshot(limit=400)

        response = {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "platform": platform.platform(),
            "cwd": os.getcwd(),
            "site_paths": site_paths,
            "import_attempts": import_results,
            "installed_snapshot_sample": installed_snapshot,
            "sys_path": sys.path[:50],
            "loaded_modules_sample": sorted(list(sys.modules.keys()))[:150],
        }
        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(content={"error": repr(e), "traceback": tb}, status_code=500)

@app.get("/openapi.json")
async def openapi_json():
    return app.openapi()

@app.get("/tryclient")
async def tryclient():
    """Small test endpoint for trying a simple import of Coinbase client."""
    names = ["coinbase_advanced_py", "coinbase_advanced", "coinbase"]
    results = {}
    for n in names:
        try:
            mod = importlib.import_module(n)
            results[n] = {"imported": True, "repr": repr(mod)[:200]}
        except Exception as e:
            results[n] = {"imported": False, "error": repr(e)}
    return results

# -----------------------------
# Example client instantiation (optional)
# -----------------------------
# if CLIENT_CLASS:
#     client = CLIENT_CLASS(api_key=os.getenv("API_KEY"), api_secret=os.getenv("API_SECRET"))
#     log.info("Coinbase client instantiated")
