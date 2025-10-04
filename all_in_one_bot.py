# all_in_one_bot.py
# Single-file diagnostic + simple FastAPI app for Coinbase import troubleshooting.
# Overwrite your current entrypoint with this file, deploy, then visit /diag2.

import sys
import os
import platform
import traceback
import importlib
import importlib.util
import pkgutil
import logging
from typing import Dict, Any

try:
    # Python 3.8+ standard API for distribution metadata
    from importlib import metadata as importlib_metadata
except Exception:
    import importlib_metadata  # type: ignore

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("all_in_one_bot")

app = FastAPI(title="NIJA Diagnostic + Bot (minimal)", version="1.0")

# --- Utility functions -----------------------------------------------------

def try_import(module_name: str) -> Dict[str, Any]:
    """Try to import module_name and return structured result (no exception escapes)."""
    out = {"module": module_name, "found": False, "spec": None, "error": None, "attrs_sample": None}
    try:
        spec = importlib.util.find_spec(module_name)
        out["spec"] = None if spec is None else {"name": spec.name, "origin": getattr(spec, "origin", None)}
        module = importlib.import_module(module_name)
        out["found"] = True
        # sample attributes to help debugging
        out["attrs_sample"] = sorted([a for a in dir(module) if not a.startswith("_")])[:60]
    except Exception as e:
        out["error"] = repr(e)
    return out

def snapshot_site_paths() -> list:
    """Return likely site-packages paths for the current interpreter/environment."""
    paths = []
    try:
        import site
        # getsitepackages may not exist in some environments (virtualenv in some hosts),
        # so guard it.
        if hasattr(site, "getsitepackages"):
            paths.extend(site.getsitepackages())
        if hasattr(site, "getusersitepackages"):
            paths.append(site.getusersitepackages())
    except Exception:
        pass
    # fallback: use any sys.path entries that look like site-packages
    paths.extend([p for p in sys.path if "site-packages" in str(p) or "dist-packages" in str(p)])
    # de-duplicate while preserving order
    seen = set()
    out = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out

def installed_distributions_snapshot(names=None):
    """Return metadata for installed distributions relevant to the troubleshooting names."""
    out = {}
    try:
        dists = list(importlib_metadata.distributions())
        # if specific names provided, filter
        for dist in dists:
            key = dist.metadata["Name"] if "Name" in dist.metadata else dist.name
            if names is None or any(n.lower() in key.lower() for n in names):
                try:
                    top_level = dist.read_text("top_level.txt")
                    top_level_list = [s.strip() for s in (top_level or "").splitlines() if s.strip()]
                except Exception:
                    top_level_list = []
                out[key] = {
                    "version": dist.version,
                    "metadata_name": key,
                    "top_level": top_level_list,
                    "location": getattr(dist, "locate_file", lambda x: None)(".")  # best-effort
                }
    except Exception as e:
        out["error"] = repr(e)
    return out

def small_pkgutil_snapshot(limit=400):
    """Return a brief snapshot of modules discoverable by pkgutil.iter_modules()."""
    out = []
    try:
        for i, info in enumerate(pkgutil.iter_modules()):
            out.append({"name": info.name, "ispkg": bool(info.ispkg), "finder": type(info.module_finder).__name__})
            if i + 1 >= limit:
                break
    except Exception as e:
        out = [{"error": repr(e)}]
    return out

# --- End utilities ---------------------------------------------------------

@app.get("/")
async def root():
    return {
        "status": "OK",
        "message": "NIJA diagnostic app is running",
        "python": sys.version,
        "platform": platform.platform(),
        "cwd": os.getcwd(),
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/modules")
async def modules():
    """Short snapshot of loaded / available modules."""
    return {
        "python_version": sys.version,
        "top_loaded_count": len(sys.modules),
        "top_loaded_sample": sorted(list(sys.modules.keys()))[:200],
    }

@app.get("/tryclient")
async def tryclient():
    """
    Quick endpoint that attempts a few obvious coinbase imports and returns results.
    Useful to paste back quickly.
    """
    candidate_names = ["coinbase_advanced_py", "coinbase_advanced", "coinbase", "coinbase.wallet", "coinbase.wallet.client"]
    results = {n: try_import(n) for n in candidate_names}
    return results

@app.get("/diag2")
async def diag2():
    """
    Full diagnostic endpoint. Paste this JSON back here when you redeploy.
    """
    try:
        candidate_imports = [
            "coinbase_advanced_py",
            "coinbase_advanced",
            "coinbase_advanced_py.client",
            "coinbase_advanced.client",
            "coinbase.wallet",
            "coinbase.wallet.client",
            "coinbase",
        ]

        import_attempts = {name: try_import(name) for name in candidate_imports}

        # check distributions relevant to coinbase
        dists = installed_distributions_snapshot(names=["coinbase", "coinbase-advanced", "coinbase-advanced-py", "coinbase_advanced"])

        response = {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "platform": platform.platform(),
            "cwd": os.getcwd(),
            "site_paths": snapshot_site_paths(),
            "sys_path_sample": sys.path[:60],
            "import_attempts": import_attempts,
            "installed_distributions_relevant": dists,
            "pkgutil_snapshot_sample": small_pkgutil_snapshot(limit=200),
            "notes": [
                "If coinbase-advanced-py distribution is present but import name coinbase_advanced_py isn't found, check top-level package names (some dists install a 'coinbase' package).",
                "Ensure your entrypoint file contains only Python code — do not paste shell commands like `find . -name ...` into Python files."
            ],
        }
        log.info("diag2 requested; returning diagnostic JSON.")
        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        tb = traceback.format_exc()
        log.error("diag2 failed: %s", tb)
        return JSONResponse(content={"error": repr(e), "traceback": tb}, status_code=500)

# --- If you want to include minimal bot startup logic, put it after the endpoints above.
# Keep it minimal so the app boots even when coinbase client isn't available.
def try_init_coinbase_client():
    """
    Attempt to construct a client object from known packages — purely diagnostic.
    Returns a dict describing the best attempt (no network calls).
    """
    result = {"success": False, "attempts": []}
    # Order of attempts: coinbase_advanced_py (preferred), coinbase_advanced, coinbase.wallet, coinbase
    attempts = [
        ("coinbase_advanced_py", "Client"),
        ("coinbase_advanced", "Client"),
        ("coinbase.wallet.client", "Client"),
        ("coinbase", "Client"),  # older coinbase library naming
    ]
    for module_name, attr in attempts:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                result["attempts"].append({module_name: "spec_not_found"})
                continue
            mod = importlib.import_module(module_name)
            if hasattr(mod, attr):
                result["attempts"].append({module_name: f"has_attr_{attr}"})
                try:
                    # Do NOT instantiate with keys — just show repr of class/obj
                    cls = getattr(mod, attr)
                    result["attempts"].append({module_name + "." + attr: repr(cls)[:400]})
                    result["success"] = True
                    result["client_module"] = module_name
                    break
                except Exception as e:
                    result["attempts"].append({module_name + "." + attr: "imported_but_could_not_get_repr: " + repr(e)})
            else:
                result["attempts"].append({module_name: f"imported_no_attr_{attr}"})
        except Exception as e:
            result["attempts"].append({module_name: "import_failed: " + repr(e)})
    return result

# run minimal diagnostic at import time to log to server logs
try:
    coinbase_diag = try_init_coinbase_client()
    log.info("Coinbase import attempts summary keys: %s", list(coinbase_diag.get("attempts", [])[:6]))
    log.info("Startup coinbase client available: %s", coinbase_diag.get("success", False))
except Exception:
    log.exception("Unexpected error during coinbase init diagnostic.")

# If you have a real bot, you can import its run loop here conditionally, e.g.:
# if coinbase_diag.get("success"):
#     from my_real_bot import start_bot
#     start_bot(client=...)   # but do this carefully; keep app startup fast.

# End of file
