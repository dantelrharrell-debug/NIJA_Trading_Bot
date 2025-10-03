from fastapi import FastAPI, Request
import sys, site, importlib
import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="NIJA DIAGNOSTIC BOT")

# ---- Diagnostic endpoint ----
@app.get("/diag")
def diag():
    info = {}
    info['python_executable'] = sys.executable
    info['python_version'] = sys.version
    info['sys_path_first_10'] = sys.path[:10]
    try:
        info['site_packages'] = site.getsitepackages()
    except Exception as e:
        info['site_packages_error'] = str(e)
    # Try importing coinbase modules
    candidates = [
        "coinbase_advanced_py",
        "coinbase_advanced",
        "coinbase_advanced_py.client",
        "coinbase_advanced.client",
        "coinbase_advanced_py.core",
        "coinbase_advanced.core",
        "coinbase",
        "coinbase.wallet"
    ]
    imports = {}
    for name in candidates:
        try:
            m = importlib.import_module(name)
            imports[name] = {"ok": True, "file": getattr(m, "__file__", None)}
        except Exception as e:
            imports[name] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    info['imports'] = imports
    return info

# ---- Safe trading placeholder ----
SANDBOX = True
ENABLE_TRADING = False
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

try:
    import coinbase_advanced_py as cb
    client = cb.Client(api_key=API_KEY, api_secret=API_SECRET, sandbox=SANDBOX)
    coinbase_status = "Coinbase Advanced client initialized!"
except Exception as e:
    client = None
    coinbase_status = f"Coinbase init failed: {e}"

@app.get("/")
def root():
    return {"status":"ok","message":"NIJA Trading Bot is live!"}

@app.get("/check-coinbase")
def check_coinbase():
    return {"status":"ok","message": coinbase_status}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    if not client:
        return {"status":"error","message":"Client not ready."}
    if not ENABLE_TRADING:
        return {"status":"ok","message":"Trading is disabled. Received payload.", "payload": data}
    return {"status":"ok","message":"Trade executed (placeholder)", "payload": data}
