import os
import sys
import platform
import logging
import traceback
import importlib
import importlib.util
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# --------------------------
# Logging setup
# --------------------------
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger("nija_trading_bot")

# --------------------------
# Robust Coinbase Client Loader
# --------------------------
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

for mod_name, attr in candidates:
    try:
        spec = importlib.util.find_spec(mod_name)
        if spec is None:
            log.debug("spec not found for %s", mod_name)
            continue
        m = importlib.import_module(mod_name)
        if hasattr(m, attr):
            CLIENT_CLASS = getattr(m, attr)
            CLIENT_MODULE = mod_name
            log.info("Found %s in %s", attr, mod_name)
            break
        cand, cand_name = find_likely_client_in_module(m)
        if cand:
            CLIENT_CLASS = cand
            CLIENT_MODULE = f"{mod_name}.{cand_name}"
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

# --------------------------
# FastAPI app
# --------------------------
app = FastAPI(title="NIJA Trading Bot", version="1.0")

# --------------------------
# Helpers
# --------------------------
def get_client():
    if CLIENT_CLASS is None:
        return None
    api_key = os.getenv("API_KEY")
    api_secret = os.getenv("API_SECRET")
    if not api_key or not api_secret:
        log.warning("API_KEY or API_SECRET missing in environment")
        return None
    try:
        client = CLIENT_CLASS(api_key=api_key, api_secret=api_secret)
        return client
    except Exception as e:
        log.error("Failed to instantiate client: %s", repr(e))
        return None

def try_import(name):
    """Try to import module, return dict with status and top-level attrs."""
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

# --------------------------
# Endpoints
# --------------------------
@app.get("/")
@app.head("/")
async def root():
    """Health check endpoint for Render."""
    return JSONResponse({"status": "bot alive"}, status_code=200)

@app.get("/diag")
async def diag():
    """Full diagnostic info for installed packages and modules."""
    try:
        site_paths = []
        try:
            import site
            site_paths = site.getsitepackages() if hasattr(site, "getsitepackages") else site.getusersitepackages()
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

        response = {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "platform": platform.platform(),
            "cwd": os.getcwd(),
            "site_paths": site_paths,
            "import_attempts": import_results,
            "sys_path": sys.path[:50],
            "loaded_modules_sample": sorted(list(sys.modules.keys()))[:150],
        }
        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(content={"error": repr(e), "traceback": tb}, status_code=500)

@app.get("/tryclient")
async def tryclient():
    """Quick test if Coinbase client can be instantiated."""
    client = get_client()
    if client:
        return {"client_available": True, "repr": repr(client)[:200]}
    else:
        return {"client_available": False}

@app.post("/webhook")
async def webhook(request: Request):
    """Placeholder webhook endpoint for TradingView signals."""
    try:
        payload = await request.json()
        log.info("Webhook received: %s", payload)
        # TODO: insert trading logic here using get_client()
        return {"status": "received", "payload": payload}
    except Exception as e:
        tb = traceback.format_exc()
        log.error("Webhook error: %s", tb)
        return JSONResponse(content={"error": repr(e), "traceback": tb}, status_code=500)

# --------------------------
# Startup check
# --------------------------
@app.on_event("startup")
async def startup_event():
    client = get_client()
    available = client is not None
    log.info("Startup coinbase client available: %s", available)
