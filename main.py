# main.py
import os
import sys
import pkgutil
import traceback
from fastapi import FastAPI, BackgroundTasks
from dotenv import load_dotenv
import time
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("nija")

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

app = FastAPI(title="NIJA Trading Bot (resilient)")

# runtime state
cb_client = None
cb_import_name = None
diagnostic_mode = True
installed_modules_snapshot = None

def snapshot_installed():
    try:
        mods = sorted([m.name for m in pkgutil.iter_modules()])
        return mods[:400]
    except Exception as e:
        return f"pkgutil error: {e}"

def try_import_coinbase():
    """
    Attempt resilient imports for the Coinbase Advanced library.
    Sets cb_client global if successful.
    """
    global cb_client, cb_import_name, diagnostic_mode
    candidates = [
        "coinbase_advanced_py",
        "coinbase_advanced",
        "coinbase_advanced_py.client",
        "coinbase_advanced.client",
        "coinbase_advanced_py.core",
        "coinbase_advanced.core",
    ]
    installed = snapshot_installed()
    log.info("Installed modules (short): %s", installed[:40] if isinstance(installed, list) else installed)
    for name in candidates:
        try:
            mod = __import__(name, fromlist=["*"])
            log.info("Imported candidate module: %s -> %s", name, getattr(mod, "__name__", str(mod)))
            # try to find a Client class or factory
            Client = None
            if hasattr(mod, "Client"):
                Client = getattr(mod, "Client")
            elif hasattr(mod, "CoinbaseAdvanced"):
                Client = getattr(mod, "CoinbaseAdvanced")
            elif hasattr(mod, "CoinbaseAdvancedClient"):
                Client = getattr(mod, "CoinbaseAdvancedClient")

            if Client:
                # attempt to instantiate (but don't crash if keys missing)
                try:
                    if API_KEY and API_SECRET:
                        client = Client(api_key=API_KEY, api_secret=API_SECRET)
                    else:
                        # some libs accept positional args; try both forms
                        try:
                            client = Client(API_KEY, API_SECRET)
                        except Exception:
                            client = Client(api_key=API_KEY, api_secret=API_SECRET)
                    cb_client = client
                    cb_import_name = name
                    diagnostic_mode = False
                    log.info("Coinbase client created from %s", name)
                    return True
                except Exception as e:
                    log.warning("Imported module %s but failed to instantiate Client: %s", name, e)
                    # keep trying other candidates
            else:
                log.info("Module %s loaded but no Client/CoinbaseAdvanced class found.", name)
        except Exception as e:
            # don't fail import process
            log.debug("Import attempt failed for %s : %s", name, e)
            continue

    # none worked
    cb_client = None
    diagnostic_mode = True
    log.error("Could not import any Coinbase Advanced module. Tried: %s", candidates)
    log.error("Installed modules (first 80): %s", installed[:80] if isinstance(installed, list) else installed)
    return False

@app.on_event("startup")
async def startup_event():
    # Print python info and try import once
    log.info("Python executable: %s", sys.executable)
    log.info("Python version: %s", sys.version.replace('\n',' '))
    installed = snapshot_installed()
    log.info("Snapshot top-level modules (first 80): %s", installed[:80] if isinstance(installed, list) else installed)
    try_import_coinbase()

@app.get("/")
async def root():
    return {
        "status": "ok",
        "diagnostic_mode": diagnostic_mode,
        "coinbase_imported_from": cb_import_name,
    }

@app.get("/debug")
async def debug_info():
    return {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "diagnostic_mode": diagnostic_mode,
        "coinbase_imported_from": cb_import_name,
        "installed_sample": snapshot_installed()[:120],
        "sys_path_sample": sys.path[:8],
    }

@app.get("/attempt-import")
async def attempt_import(background: BackgroundTasks):
    """
    Trigger another attempt to import Coinbase (useful after changing requirements and redeploy).
    """
    background.add_task(try_import_coinbase)
    return {"status": "re-attempting import in background"}

# Safe test endpoint for balance (will not crash if no client)
@app.get("/balance")
async def balance():
    if not cb_client:
        return {"error": "Coinbase client not initialized (diagnostic mode)."}
    # Attempt common balance call — different libs use different method names so try safe calls
    try:
        if hasattr(cb_client, "get_accounts"):
            accounts = cb_client.get_accounts()
            return {"accounts_count": len(accounts)}
        if hasattr(cb_client, "get_account"):
            # fallback single-call
            a = cb_client.get_account("USD")
            return {"account": a}
        # unknown client API
        return {"info": "client present but no known balance method"}
    except Exception as e:
        return {"error": str(e)}

# Example endpoint to place a market order (VERY SAFE: checks diagnostic mode)
@app.post("/trade")
async def trade(symbol: str = "BTC-USD", side: str = "buy", amount_usd: float = 10.0):
    if diagnostic_mode or not cb_client:
        return {"error": "Trading disabled: bot in diagnostic mode (Coinbase client unavailable)."}
    try:
        # Try known client order shapes
        if hasattr(cb_client, "place_order"):
            order = cb_client.place_order(product_id=symbol, side=side, order_type="market", funds=str(amount_usd))
            return {"ok": True, "order": str(order)}
        elif hasattr(cb_client, "create_order"):
            order = cb_client.create_order(symbol=symbol, side=side, amount=amount_usd)
            return {"ok": True, "order": str(order)}
        else:
            return {"error": "Client present but no supported order method found."}
    except Exception as e:
        return {"error": f"order failed: {e}", "trace": traceback.format_exc()}

# Keep app running — uvicorn will serve this
