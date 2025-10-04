# main.py - diagnostic FastAPI app for Render
# Paste this file as your app entrypoint (replacing previous coinbase import).
# Endpoints: / (health), /modules (snapshot), /diag2 (detailed), /tryclient (quick import tests)

import sys
import os
import platform
import json
import traceback
import logging
import pkgutil
import importlib
import importlib.util
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("nija_diag")

# Robust dynamic Coinbase client loader (replaces direct "from coinbase_advanced_py import Client")
CLIENT_CLASS = None
CLIENT_MODULE = None

candidates = [
    ("coinbase_advanced_py", "Client"),
    ("coinbase_advanced", "Client"),
    ("coinbase.wallet.client", "Client"),
    ("coinbase.client", "Client"),
    ("coinbase", "Client"),
]

for mod_name, attr in candidates:
    try:
        spec = importlib.util.find_spec(mod_name)
        if spec is None:
            # module not found; continue
            log.debug("spec not found for %s", mod_name)
            continue
        m = importlib.import_module(mod_name)
        if hasattr(m, attr):
            CLIENT_CLASS = getattr(m, attr)
            CLIENT_MODULE = mod_name
            log.info("Found Coinbase client attr %s in module %s", attr, mod_name)
            break
        else:
            log.debug("%s imported but has no %s", mod_name, attr)
    except Exception as e:
        log.debug("Import attempt failed for %s: %s", mod_name, e)

if CLIENT_CLASS is None:
    log.warning("No Coinbase client class found among candidates. Running in diagnostic mode.")
else:
    log.info("Using Coinbase client class %s from module %s",
             getattr(CLIENT_CLASS, "__name__", str(CLIENT_CLASS)), CLIENT_MODULE)

# FastAPI diagnostic app
app = FastAPI(title="NIJA Diagnostic", version="1.0")

def try_import(name):
    """
    Try to import a module by name, return dict with status and details.
    Does not raise.
    """
    out = {"name": name, "found": False, "import_error": None, "attrs": None, "spec": None}
    try:
        spec = importlib.util.find_spec(name)
        out["spec"] = None if spec is None else {"name": spec.name, "origin": getattr(spec, "origin", None)}
        module = importlib.import_module(name)
        out["found"] = True
        # sample top-level attrs to show what's available
        out["attrs"] = sorted([a for a in dir(module) if not a.startswith("_")])[:200]
    except Exception as e:
        out["import_error"] = repr(e)
    return out

def installed_packages_snapshot(limit=200):
    """
    Return list of installed packages from pkgutil and sys.modules sampling.
    This doesn't call pip but gives a useful view of modules present.
    """
    pkgs = []
    try:
        for m in pkgutil.iter_modules():
            pkgs.append({"name": m.name, "ispkg": bool(m.ispkg), "module_finder": type(m.module_finder).__name__})
            if len(pkgs) >= limit:
                break
    except Exception as e:
        pkgs = [{"error": f"pkgutil.iter_modules failure: {repr(e)}"}]
    return pkgs

@app.get("/")
async def root():
    return {"status": "OK", "message": "Diagnostic app running", "python": sys.version, "platform": platform.platform()}

@app.get("/modules")
async def modules():
    """Return small snapshot of top-level modules loaded and available (short)."""
    top_loaded = sorted(list(sys.modules.keys()))[:200]
    return {"python_version": sys.version, "top_loaded_modules_count": len(sys.modules), "top_loaded_sample": top_loaded}

@app.get("/diag2")
async def diag2():
    """
    Full diagnostic endpoint intended for you to paste here.
    It will try multiple coinbase import names and show site-packages paths.
    """
    try:
        # site-packages paths
        site_paths = []
        try:
            import site
            # getsitepackages may not be available in some envs (virtual envs) so handle gracefully
            if hasattr(site, "getsitepackages"):
                site_paths = site.getsitepackages()
            else:
                # fallback to user site packages
                site_paths = [site.getusersitepackages()] if hasattr(site, "getusersitepackages") else []
        except Exception:
            # fallback to scanning sys.path
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

        # pip-installed packages via pkgutil snapshot (not pip list, but helpful)
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
            # list first 150 loaded modules to inspect for unexpected names
            "loaded_modules_sample": sorted(list(sys.modules.keys()))[:150],
            "selected_client_module": CLIENT_MODULE,
            "selected_client_class": getattr(CLIENT_CLASS, "__name__", None) if CLIENT_CLASS else None
        }
        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(content={"error": repr(e), "traceback": tb}, status_code=500)

@app.get("/openapi.json")
async def openapi_json():
    return app.openapi()

# Helpful small test endpoint for trying a simple import of coinbase modules
@app.get("/tryclient")
async def tryclient():
    names = ["coinbase_advanced_py", "coinbase_advanced", "coinbase", "coinbase.wallet", "coinbase.wallet.client"]
    results = {}
    for n in names:
        try:
            mod = importlib.import_module(n)
            # give repr and sample attributes
            results[n] = {"imported": True, "repr": repr(mod)[:200], "sample_attrs": sorted([a for a in dir(mod) if not a.startswith("_")])[:40]}
        except Exception as e:
            results[n] = {"imported": False, "error": repr(e)}
    # also return which client the loader found
    results["_selected_client_module"] = CLIENT_MODULE
    results["_selected_client_class"] = getattr(CLIENT_CLASS, "__name__", None) if CLIENT_CLASS else None
    return results
