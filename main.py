# main.py - diagnostic FastAPI app for Render
# Replace your existing entrypoint with this, deploy, then visit /diag2

import sys
import json
import os
import platform
import importlib
import importlib.util
import pkgutil
import traceback
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="NIJA Diagnostic", version="1.0")

def try_import(name):
    """
    Try to import a module by name, return dict with status and details.
    Does not raise.
    """
    out = {"name": name, "found": False, "import_error": None, "attrs": None}
    try:
        spec = importlib.util.find_spec(name)
        out["find_spec"] = None if spec is None else {"name": spec.name, "origin": getattr(spec, "origin", None)}
        module = importlib.import_module(name)
        out["found"] = True
        # sample top-level attrs to show what's available
        out["attrs"] = sorted([a for a in dir(module) if not a.startswith("_")])[:40]
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
            site_paths = site.getsitepackages() if hasattr(site, "getsitepackages") else site.getusersitepackages()
        except Exception:
            # fallback
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
        }
        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(content={"error": repr(e), "traceback": tb}, status_code=500)

@app.get("/openapi.json")
async def openapi_json():
    return app.openapi()

# Helpful small test endpoint for trying a simple import of coinbase_advanced_py.Client
@app.get("/tryclient")
async def tryclient():
    names = ["coinbase_advanced_py", "coinbase_advanced", "coinbase"]
    results = {}
    for n in names:
        try:
            mod = importlib.import_module(n)
            results[n] = {"imported": True, "repr": repr(mod)[:200]}
        except Exception as e:
            results[n] = {"imported": False, "error": repr(e)}
    return results
