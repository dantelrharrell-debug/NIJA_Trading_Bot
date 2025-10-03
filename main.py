# main.py - safe resilient startup (diagnostic)
from fastapi import FastAPI
import os, sys, importlib, traceback, pkgutil

app = FastAPI(title="NIJA Trading Bot (diagnostic)")

print("=== NIJA Trading Bot starting ===")
print("Python executable:", sys.executable)
print("Python version:", sys.version)

# Try multiple candidate names for the Coinbase Advanced lib
_coinbase_module = None
_import_name = None
_candidates = [
    "coinbase_advanced_py",
    "coinbase_advanced",
    "coinbase_advanced_py.client",
    "coinbase_advanced.client",
    "coinbase_advanced_py.core",
    "coinbase_advanced.core",
]

for name in _candidates:
    try:
        mod = importlib.import_module(name)
        _coinbase_module = mod
        _import_name = name
        print("✅ Imported Coinbase candidate:", name)
        break
    except Exception as e:
        print(f" - Cannot import {name}: {type(e).__name__}: {e}")

if _coinbase_module is None:
    try:
        installed = sorted([m.name for m in pkgutil.iter_modules()])
        print("DEBUG installed top-level modules (first 200):", installed[:200])
    except Exception as e:
        print("DEBUG pkgutil failed:", e)
    print("❌ Could not import any Coinbase Advanced module. Bot will continue in diagnostic mode.")
    client = None
else:
    client = None
    try:
        if hasattr(_coinbase_module, "Client"):
            ClientClass = getattr(_coinbase_module, "Client")
        elif hasattr(_coinbase_module, "CoinbaseAdvanced"):
            ClientClass = getattr(_coinbase_module, "CoinbaseAdvanced")
        else:
            ClientClass = None

        if ClientClass is not None:
            API_KEY = os.getenv("API_KEY")
            API_SECRET = os.getenv("API_SECRET")
            SANDBOX = os.getenv("SANDBOX", "true").lower() in ("1", "true", "yes")
            if API_KEY and API_SECRET:
                try:
                    try:
                        client = ClientClass(api_key=API_KEY, api_secret=API_SECRET, sandbox=SANDBOX)
                    except TypeError:
                        client = ClientClass(API_KEY, API_SECRET)
                    print("✅ Coinbase client instantiated from:", _import_name)
                except Exception as e:
                    print("❌ Failed to instantiate Coinbase client:", type(e).__name__, e)
            else:
                print("⚠ API_KEY / API_SECRET not set — client not created.")
        else:
            print("⚠ Coinbase module imported but no Client/CoinbaseAdvanced class found.")
    except Exception:
        print("❌ Unexpected error preparing client:")
        traceback.print_exc()
        client = None

@app.get("/")
def root():
    return {"status": "ok", "message": "NIJA Trading Bot (diagnostic) — process running"}

@app.get("/check-coinbase")
def check_coinbase():
    if client is None:
        return {
            "status": "error",
            "message": "Coinbase client not available. Check requirements.txt and installed modules.",
            "imported_module": _import_name,
        }
    try:
        return {"status": "ok", "message": "Coinbase client present", "client_type": str(type(client))}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected client error: {type(e).__name__}: {e}"}
