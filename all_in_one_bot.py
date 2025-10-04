# all_in_one_bot.py
import os
import sys
import asyncio
import logging
import importlib
import pkgutil
from typing import Optional, Dict, Any

from fastapi import FastAPI

# --- logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger("all_in_one_bot")

# --- env ---
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
PORT = int(os.getenv("PORT", "10000"))

app = FastAPI(title="NIJA Bot (diagnostic friendly)")

# Global state
coinbase_client = None
coinbase_import_attempts: Dict[str, Any] = {}
trading_task: Optional[asyncio.Task] = None
trading_running = False

# Candidate import names to try (we will not import at module-import time)
IMPORT_CANDIDATES = [
    ("coinbase_advanced_py", "Client"),
    ("coinbase_advanced", "Client"),
    ("coinbase_advanced_py.client", "Client"),
    ("coinbase_advanced.client", "Client"),
    ("coinbase", "Client"),
    ("coinbase.wallet.client", "Client"),
]

def list_coinbase_top_level() -> Dict[str, Any]:
    """
    Diagnostic: find coinbase-related top-level modules visible to the running interpreter.
    Also return distributions that mention 'coinbase' if importlib.metadata is available.
    """
    found = {"pkgutil_modules": [], "site_packages_listing": [], "distributions": []}
    try:
        for m in pkgutil.iter_modules():
            name = m.name
            if "coinbase" in name.lower():
                found["pkgutil_modules"].append(name)
    except Exception as e:
        LOG.exception("pkgutil.iter_modules failed: %s", e)

    # list files in site-packages that start with coinbase*
    try:
        for p in sys.path:
            try:
                if not p or "site-packages" not in p:
                    continue
                for fn in os.listdir(p):
                    if fn.lower().startswith("coinbase"):
                        found["site_packages_listing"].append(os.path.join(p, fn))
            except Exception:
                continue
    except Exception as e:
        LOG.exception("listing site-packages failed: %s", e)

    # importlib.metadata to list installed distributions (Python 3.8+)
    try:
        try:
            from importlib import metadata as importlib_metadata
        except Exception:
            import importlib_metadata
        for dist in importlib_metadata.distributions():
            name = dist.metadata["Name"] if "Name" in dist.metadata else dist.metadata.get("name", "")
            if name and "coinbase" in name.lower():
                found["distributions"].append(name)
    except Exception:
        # best-effort; ignore failures
        pass

    return found

def try_import_coinbase():
    """
    Try a set of candidate module names and attributes. Return (client_instance_or_None, attempts_dict).
    This function purposely does not run at module import time (call it in startup event).
    """
    attempts = {}
    client = None

    for mod_name, attr in IMPORT_CANDIDATES:
        try:
            spec = importlib.util.find_spec(mod_name)
            if spec is None:
                attempts[mod_name] = {"status": "not_found", "detail": "find_spec returned None"}
                continue

            module = importlib.import_module(mod_name)
            attempts[mod_name] = {"status": "imported", "module": mod_name}

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

@app.on_event("startup")
async def startup_event():
    global coinbase_client, coinbase_import_attempts
    LOG.info("Application startup: attempting to import coinbase client (lazy).")
    coinbase_client, coinbase_import_attempts = try_import_coinbase()
    if coinbase_client:
        LOG.info("Coinbase client ready.")
    else:
        LOG.warning("No usable Coinbase client found. Running in diagnostic mode.")
    LOG.info("Startup complete.")

@app.get("/")
async def root():
    return {
        "status": "running",
        "coinbase_client": bool(coinbase_client),
        "import_attempts": coinbase_import_attempts,
        "diagnostic": list_coinbase_top_level()
    }

@app.get("/diag")
async def diag():
    # same as root but verbose
    return {
        "coinbase_client": bool(coinbase_client),
        "import_attempts": coinbase_import_attempts,
        "diagnostic": list_coinbase_top_level(),
        "python_executable": sys.executable,
        "sys_path": sys.path[:6]
    }

@app.post("/start_trading")
async def start_trading():
    global trading_task, trading_running
    if trading_running:
        return {"status": "already_running"}
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
    global trading_running
    LOG.info("Trading loop started (placeholder).")
    try:
        while True:
            if not coinbase_client:
                LOG.info("Trading loop: no coinbase client; diagnostic sleep 30s.")
                await asyncio.sleep(30)
                continue

            # ===== REPLACE THIS BLOCK WITH REAL STRATEGY =====
            try:
                # Safe call example — adjust to your client's API
                if hasattr(coinbase_client, "get_usd_balance"):
                    try:
                        bal = coinbase_client.get_usd_balance()
                        LOG.info("USD balance: %s", bal)
                    except Exception as e:
                        LOG.warning("Balance check failed: %s", e)
                else:
                    LOG.info("Client present but get_usd_balance not found; heartbeat.")
            except Exception:
                LOG.exception("Error in trading step.")
            # ==================================================

            await asyncio.sleep(10)
    except asyncio.CancelledError:
        LOG.info("Trading loop cancelled.")
    except Exception:
        LOG.exception("Unhandled error in trading loop.")
    finally:
        trading_running = False
        LOG.info("Trading loop ended.")
