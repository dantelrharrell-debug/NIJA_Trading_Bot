# all_in_one_bot.py
import os
import time
import asyncio
import importlib
import logging
from typing import Optional

from fastapi import FastAPI, BackgroundTasks
from dotenv import load_dotenv

load_dotenv()

LOG = logging.getLogger("nija_bot")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Config
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
PORT = int(os.getenv("PORT", "10000"))

# App
app = FastAPI(title="NIJA Trading Bot (diagnostic-friendly)")

# Globals to hold client & status
coinbase_client = None
coinbase_import_attempts = {}
trading_task: Optional[asyncio.Task] = None
trading_running = False

# Try import variants that might exist on the system.
IMPORT_VARIANTS = [
    ("coinbase_advanced_py", "Client"),
    ("coinbase_advanced", "Client"),
    ("coinbase_advanced_py.client", "Client"),
    ("coinbase_advanced.client", "Client"),
    ("coinbase", "Client"),
]

def try_import_coinbase():
    """
    Attempt to import the Coinbase Advanced client using several common module names.
    Returns an instantiated client (or None) and a dict describing attempts.
    """
    attempts = {}
    client = None

    for mod_name, attr in IMPORT_VARIANTS:
        try:
            spec = importlib.util.find_spec(mod_name)
            if spec is None:
                attempts[mod_name] = {"status": "not_found", "detail": "find_spec returned None"}
                continue

            module = importlib.import_module(mod_name)
            attempts[mod_name] = {"status": "imported", "module": mod_name}
            LOG.info("Imported module %s", mod_name)

            # if the module exposes a Client class or attr, try to instantiate
            if hasattr(module, attr):
                ClientClass = getattr(module, attr)
                try:
                    client = ClientClass(API_KEY, API_SECRET)
                    attempts[mod_name]["client_instantiated"] = True
                    LOG.info("Instantiated client from %s.%s", mod_name, attr)
                    break
                except Exception as e:
                    attempts[mod_name]["client_error"] = repr(e)
                    LOG.warning("Failed to instantiate client from %s: %s", mod_name, e)
            else:
                attempts[mod_name]["has_attr"] = False
        except Exception as e:
            attempts[mod_name] = {"status": "import_failed", "detail": repr(e)}
            LOG.exception("Import failed for %s", mod_name)

    return client, attempts

# Initialize (on import) but keep tolerant.
coinbase_client, coinbase_import_attempts = try_import_coinbase()
if coinbase_client:
    LOG.info("Coinbase client ready.")
else:
    LOG.warning("No usable Coinbase client found. Running in diagnostic mode. Import attempts: %s", coinbase_import_attempts)

# Health endpoint
@app.get("/")
async def root():
    return {
        "status": "running",
        "coinbase_client": bool(coinbase_client),
        "import_attempts": coinbase_import_attempts
    }

@app.get("/status")
async def status():
    return {
        "trading_running": trading_running,
        "coinbase_client": bool(coinbase_client)
    }

@app.post("/start_trading")
async def start_trading(background_tasks: BackgroundTasks):
    global trading_task, trading_running
    if trading_running:
        return {"status": "already_running"}
    # Start background loop
    loop = asyncio.get_running_loop()
    trading_task = loop.create_task(trading_loop())
    trading_running = True
    return {"status": "started"}

@app.post("/stop_trading")
async def stop_trading():
    global trading_task, trading_running
    if not trading_running:
        return {"status": "not_running"}
    trading_task.cancel()
    trading_running = False
    return {"status": "stopped"}

async def trading_loop():
    """
    Basic example auto-trader loop. Replace placeholder logic here with your real trading strategy.
    This function must handle exceptions and never crash the process.
    """
    global trading_running
    LOG.info("Trading loop started.")
    try:
        while True:
            # If we don't have a client, only run diagnostic checks
            if not coinbase_client:
                LOG.info("Diagnostic mode: no client. Sleeping 30s.")
                await asyncio.sleep(30)
                continue

            # ===== PLACEHOLDER STRATEGY =====
            # Example: get account balances (pseudo)
            try:
                # Replace the calls below with actual methods of the client you end up using.
                # Some clients use client.get_accounts(), client.get_balance(), etc.
                # Example diagnostic call (safe): attempt to read some attribute / method
                if hasattr(coinbase_client, "get_usd_balance"):
                    bal = coinbase_client.get_usd_balance()
                    LOG.info("USD balance: %s", bal)
                else:
                    LOG.debug("Client has no get_usd_balance; checking generic attrs")
                    # try other safe ops or just log a heartbeat
                    LOG.info("Heartbeat: client appears usable.")
            except Exception as e:
                LOG.exception("Error while querying client: %s", e)

            # Sleep before next iteration
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        LOG.info("Trading loop cancelled.")
    except Exception as e:
        LOG.exception("Unhandled error in trading loop: %s", e)
    finally:
        trading_running = False
        LOG.info("Trading loop ended.")

# On startup, log paths and pip-installed coinbase packages sample
@app.on_event("startup")
async def on_startup():
    LOG.info("Application startup complete.")
    # list candidate modules found on sys.path (diagnostic)
    import sys
    LOG.info("sys.path sample: %s", sys.path[:4])
    try:
        import pkgutil
        matches = [m.name for m in pkgutil.iter_modules() if "coinbase" in m.name.lower()]
        LOG.info("coinbase-related modules visible to pkgutil.iter_modules(): %s", matches)
    except Exception:
        LOG.exception("Failed to list modules via pkgutil.")
