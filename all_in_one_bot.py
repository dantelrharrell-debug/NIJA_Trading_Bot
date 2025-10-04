# all_in_one_bot.py
# Drop-in replacement. Paste this file and redeploy.
#
# IMPORTANT: This file intentionally does NOT "from coinbase_advanced_py import Client"
# at top level. It performs dynamic discovery at runtime to avoid ModuleNotFoundErrors.

import os
import sys
import logging
import importlib
import importlib.util
from fastapi import FastAPI, APIRouter

LOG = logging.getLogger("all_in_one_bot")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="NIJA Trading Bot (diagnostic friendly)")

# Global coinbase client placeholder
coinbase_client = None
coinbase_import_attempts = {}

def try_import_coinbase():
    """
    Robust runtime importer:
    - Inspect installed distributions with importlib.metadata for any dist with 'coinbase' in the dist name.
    - Read their top_level.txt to get actual importable package names.
    - Try to import those packages and look for common client constructors or attributes.
    Returns (client_instance_or_None, attempts_dict).
    """
    attempts = {}
    client = None

    # common fallback candidate modules and attr names
    fallback_candidates = [
        ("coinbase_advanced_py", "Client"),
        ("coinbase_advanced", "Client"),
        ("coinbase", "Client"),
        ("coinbase.wallet.client", "Client"),
    ]

    # 1) scan installed distributions via importlib.metadata for 'coinbase' in name
    try:
        try:
            from importlib import metadata as importlib_metadata  # py3.8+
        except Exception:
            import importlib_metadata as importlib_metadata  # type: ignore
        for dist in importlib_metadata.distributions():
            dist_name = (dist.metadata.get("Name") or dist.metadata.get("name") or "").strip()
            if not dist_name or "coinbase" not in dist_name.lower():
                continue

            key = f"dist:{dist_name}"
            attempts[key] = {"status": "found_distribution"}
            top_levels = []
            try:
                top = dist.read_text("top_level.txt")
                if top:
                    top_levels = [s.strip() for s in top.splitlines() if s.strip()]
                attempts[key]["top_level"] = top_levels
            except Exception as e:
                attempts[key]["top_level_error"] = repr(e)
                top_levels = []

            # try to import each top level package
            for pkg in top_levels:
                try:
                    spec = importlib.util.find_spec(pkg)
                    if spec is None:
                        attempts[key][pkg] = {"status": "not_found_by_find_spec"}
                        continue
                    module = importlib.import_module(pkg)
                    attempts[key][pkg] = {"status": "imported", "module_attrs_sample": dir(module)[:30]}
                    # try common Client attribute names
                    for attr in ("Client", "client", "CoinbaseAdvancedClient"):
                        if hasattr(module, attr):
                            ClientClass = getattr(module, attr)
                            try:
                                # Try to instantiate with environment vars; if not present, try without
                                api_key = os.getenv("COINBASE_API_KEY") or os.getenv("API_KEY")
                                api_secret = os.getenv("COINBASE_API_SECRET") or os.getenv("API_SECRET")
                                if api_key and api_secret:
                                    client = ClientClass(api_key, api_secret)
                                else:
                                    # attempt no-arg or single-arg instantiation
                                    try:
                                        client = ClientClass()
                                    except TypeError:
                                        try:
                                            client = ClientClass(api_key)
                                        except Exception:
                                            client = None
                                attempts[key][pkg]["instantiated_via"] = attr
                                if client:
                                    LOG.info("Instantiated client from dist=%s pkg=%s attr=%s", dist_name, pkg, attr)
                                    return client, attempts
                            except Exception as e:
                                attempts[key][pkg]["instantiation_error"] = repr(e)
                except Exception as e:
                    attempts[key][pkg] = {"status": "import_failed", "detail": repr(e)}
    except Exception as e:
        LOG.exception("importlib.metadata scan failed: %s", e)
        attempts["importlib_metadata_scan_error"] = repr(e)

    # 2) fallback: try fallback candidates
    for mod_name, attr in fallback_candidates:
        try:
            spec = importlib.util.find_spec(mod_name)
            if spec is None:
                attempts[mod_name] = {"status": "not_found", "detail": "find_spec returned None"}
                continue
            module = importlib.import_module(mod_name)
            attempts[mod_name] = {"status": "imported", "module_attrs_sample": dir(module)[:30]}
            if hasattr(module, attr):
                ClientClass = getattr(module, attr)
                try:
                    api_key = os.getenv("COINBASE_API_KEY") or os.getenv("API_KEY")
                    api_secret = os.getenv("COINBASE_API_SECRET") or os.getenv("API_SECRET")
                    if api_key and api_secret:
                        client = ClientClass(api_key, api_secret)
                    else:
                        try:
                            client = ClientClass()
                        except TypeError:
                            client = None
                    attempts[mod_name]["client_instantiated"] = bool(client)
                    if client:
                        LOG.info("Instantiated client via fallback %s.%s", mod_name, attr)
                        return client, attempts
                except Exception as e:
                    attempts[mod_name]["client_error"] = repr(e)
            else:
                attempts[mod_name]["has_attr"] = False
        except Exception as e:
            attempts[mod_name] = {"status": "import_failed", "detail": repr(e)}

    # 3) last-ditch brute-force: enumerate modules in pkgutil that contain 'coinbase' in their name
    try:
        import pkgutil
        bf = {}
        for finder, name, ispkg in pkgutil.iter_modules():
            if "coinbase" in name.lower():
                try:
                    module = importlib.import_module(name)
                    bf[name] = {"imported": True, "attrs_sample": dir(module)[:30]}
                except Exception as e:
                    bf[name] = {"imported": False, "error": repr(e)}
        if bf:
            attempts["pkgutil_bruteforce"] = bf
    except Exception as e:
        attempts["pkgutil_bruteforce_error"] = repr(e)

    return client, attempts

# Run import attempt at startup
try:
    coinbase_client, coinbase_import_attempts = try_import_coinbase()
    if coinbase_client:
        LOG.info("Coinbase client successfully initialized.")
    else:
        LOG.warning("No usable Coinbase client found. Running in diagnostic mode.")
        LOG.info("Coinbase import attempts: %s", coinbase_import_attempts)
except Exception:
    LOG.exception("Unexpected error while trying to initialize coinbase client.")
    coinbase_client = None

# Minimal endpoints for health and diag
router = APIRouter()

@router.get("/", tags=["health"])
async def root():
    return {
        "status": "ok",
        "coinbase_client": bool(coinbase_client),
    }

@router.get("/diag2", tags=["diagnostics"])
async def diag2():
    """
    Diagnostics JSON:
    - python executable & sample sys.path
    - site-packages paths and coinbase-related entries inside them
    - distributions with 'coinbase' in dist name and their top_level.txt
    - the import attempts results
    """
    res = {}
    res["python_executable"] = sys.executable
    res["python_version"] = sys.version
    res["sys_path_sample"] = sys.path[:12]

    # site-packages coinbase matches
    site_matches = []
    for p in sys.path:
        try:
            if p and "site-packages" in p and os.path.isdir(p):
                try:
                    entries = sorted([e for e in os.listdir(p) if "coinbase" in e.lower()])[:50]
                except Exception:
                    entries = []
                site_matches.append({"path": p, "entries": entries})
        except Exception:
            continue
    res["site_packages_coinbase_matches"] = site_matches

    # importlib.metadata scan for 'coinbase' in distribution names
    try:
        try:
            from importlib import metadata as importlib_metadata
        except Exception:
            import importlib_metadata as importlib_metadata  # type: ignore
        dlist = []
        for dist in importlib_metadata.distributions():
            name = (dist.metadata.get("Name") or dist.metadata.get("name") or "").strip()
            if "coinbase" in name.lower():
                item = {"dist_name": name}
                try:
                    top = dist.read_text("top_level.txt")
                    item["top_level"] = [s.strip() for s in top.splitlines() if s.strip()] if top else []
                except Exception as e:
                    item["top_level_error"] = repr(e)
                # sample files under distribution root (best-effort)
                try:
                    loc = dist.locate_file("")
                    if loc and os.path.isdir(loc):
                        item["files_sample"] = sorted([f for f in os.listdir(loc) if "coinbase" in f.lower()])[:50]
                    else:
                        item["files_sample"] = None
                except Exception as e:
                    item["files_sample_error"] = repr(e)
                dlist.append(item)
        res["distributions_with_coinbase"] = dlist
    except Exception as e:
        res["dist_scan_error"] = repr(e)

    # include the attempted import results (best-effort)
    res["coinbase_import_attempts_sample"] = coinbase_import_attempts

    return res

app.include_router(router)

# If you prefer a simple startup log
@app.on_event("startup")
async def startup_event():
    LOG.info("Startup complete. coinbase_client: %s", bool(coinbase_client))
    # Log short summary of import attempts
    try:
        LOG.info("Coinbase import attempts summary keys: %s", list(coinbase_import_attempts.keys())[:40])
    except Exception:
        pass

# Example placeholder - safe wrapper to call coinbase functions
def get_coinbase_client():
    """Return coinbase client or raise RuntimeError if missing."""
    if not coinbase_client:
        raise RuntimeError("Coinbase client not available. Check /diag2 for details.")
    return coinbase_client

# If you want an example endpoint that uses the client, keep it commented until you're ready:
# @router.get("/balance")
# async def balances():
#     c = get_coinbase_client()
#     # replace the following with the real client method:
#     return {"balances": "example - replace with real calls"}

if __name__ == "__main__":
    # quick run for local dev
    import uvicorn
    uvicorn.run("all_in_one_bot:app", host="0.0.0.0", port=int(os.getenv("PORT", 10000)), log_level="info")
