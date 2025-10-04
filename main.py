# main.py — safe Coinbase import + diagnostics (fixed "module not callable" bug)
import os
import sys
import asyncio
import logging
import pkgutil
import importlib
import traceback
from typing import Any, Dict, List, Optional
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("nija")

app = FastAPI(title="NIJA Trading Bot")

# Config from env
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
LIVE_TRADING = os.getenv("LIVE_TRADING", "false").lower() in ("1", "true", "yes")
RENT_DUE_HOURS = float(os.getenv("RENT_DUE_HOURS", "0"))

# Candidate module names to attempt
COINBASE_CANDIDATES = [
    "coinbase_advanced_py",
    "coinbase_advanced",
    "coinbase_advanced_py.client",
    "coinbase_advanced.client",
    "coinbase.wallet",
    "coinbase.wallet.client",
    "coinbase",
]

CoinbaseClientClass = None      # expected to be a class or callable factory
coinbase_client_instance = None
import_attempts: Dict[str, Dict[str, str]] = {}

def list_top_level_modules(limit: int = 200) -> List[str]:
    try:
        return [m.name for m in pkgutil.iter_modules()][:limit]
    except Exception as e:
        return [f"error_listing_modules: {e}"]

def site_packages_paths() -> List[str]:
    import site
    paths = []
    if hasattr(site, "getsitepackages"):
        paths.extend(site.getsitepackages())
    if hasattr(site, "getusersitepackages"):
        paths.append(site.getusersitepackages())
    return paths

def try_import_coinbase():
    """
    Attempt several module names. Only set CoinbaseClientClass if we find a callable/class named Client (or other
    well-known symbols). Do NOT treat an imported module itself as a callable.
    """
    global CoinbaseClientClass, import_attempts
    import_attempts = {}
    for name in COINBASE_CANDIDATES:
        try:
            spec = importlib.util.find_spec(name)
            if spec is None:
                import_attempts[name] = {"status": "not_found", "detail": "find_spec returned None"}
                continue
            mod = importlib.import_module(name)
            # gather attributes to help diagnostics
            attrs = sorted([a for a in dir(mod) if not a.startswith("_")])[:50]
            import_attempts[name] = {"status": "imported", "attrs_sample": attrs}
            # find obvious client symbols
            candidates = ["Client", "client", "CoinbaseClient", "AdvancedClient", "ClientV2"]
            for sym in candidates:
                if hasattr(mod, sym):
                    candidate = getattr(mod, sym)
                    # ensure candidate is callable (class or function) before using it
                    if callable(candidate):
                        CoinbaseClientClass = candidate
                        import_attempts[name]["selected_symbol"] = sym
                        import_attempts[name]["selected_symbol_type"] = str(type(candidate))
                        log.info("Selected client symbol %s from module %s", sym, name)
                        return import_attempts
                    else:
                        import_attempts[name]["selected_symbol_not_callable"] = sym
            # If module exports nothing usable, continue searching other names
        except Exception as e:
            import_attempts[name] = {"status": "import_failed", "detail": repr(e)}
    return import_attempts

def init_coinbase_client():
    global coinbase_client_instance
    if CoinbaseClientClass is None:
        log.info("No Coinbase client class found to initialize.")
        return None
    try:
        # try positional, then keyword
        try:
            coinbase_client_instance = CoinbaseClientClass(API_KEY, API_SECRET)
        except TypeError:
            coinbase_client_instance = CoinbaseClientClass(api_key=API_KEY, api_secret=API_SECRET)
        log.info("Coinbase client initialized successfully using %s", getattr(CoinbaseClientClass, "__name__", str(CoinbaseClientClass)))
        return coinbase_client_instance
    except Exception as e:
        log.exception("Failed to initialize coinbase client: %s", e)
        coinbase_client_instance = None
        return None

@app.on_event("startup")
async def startup_event():
    log.info("=== NIJA Trading Bot startup ===")
    log.info("python executable: %s", sys.executable)
    log.info("python version: %s", sys.version.splitlines()[0])
    log.info("cwd: %s", os.getcwd())
    log.info("site-packages paths: %s", site_packages_paths())
    log.info("top-level modules sample: %s", list_top_level_modules(80))
    try_import_coinbase()
    log.info("coinbase import attempts: %s", import_attempts)
    # only initialize if we found a callable client class
    if CoinbaseClientClass:
        init_coinbase_client()
    else:
        log.error("Could not import any usable Coinbase Advanced client class. Bot will continue in diagnostic mode.")
    if coinbase_client_instance and LIVE_TRADING:
        log.info("Starting background trading loop (LIVE_TRADING=%s).", LIVE_TRADING)
        asyncio.create_task(trading_loop())

@app.get("/")
async def root():
    return {"status": "ok", "live_trading": LIVE_TRADING, "coinbase_client": bool(coinbase_client_instance)}

@app.get("/diag")
async def diag():
    return {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "site_packages_paths": site_packages_paths(),
        "top_level_modules_sample": list_top_level_modules(120),
        "coinbase_import_attempts": import_attempts,
        "coinbase_client_initialized": coinbase_client_instance is not None,
        "env": {k: os.environ.get(k) for k in ("PORT", "LIVE_TRADING", "RENT_DUE_HOURS", "API_KEY")},
    }

# minimal safe trading loop (doesn't place orders by default)
async def check_rent_guard() -> bool:
    try:
        hours = float(os.getenv("RENT_DUE_HOURS", "0"))
        if hours <= 0:
            return True
        if hours < 1.0:
            log.warning("RENT_DUE_HOURS < 1, blocking live trading as safety measure.")
            return False
        return True
    except Exception as e:
        log.exception("Rent guard check failed: %s", e)
        return False

async def trading_loop():
    interval = int(os.getenv("TRADING_POLL_INTERVAL", "10"))
    log.info("Trading loop started with poll interval %s seconds", interval)
    while True:
        try:
            if not await check_rent_guard():
                await asyncio.sleep(30)
                continue
            if not coinbase_client_instance:
                log.error("No coinbase client instance available; trading loop exiting.")
                return
            # best-effort balance fetch (non-fatal)
            bal = "unknown"
            try:
                if hasattr(coinbase_client_instance, "get_accounts"):
                    bal = coinbase_client_instance.get_accounts()
                elif hasattr(coinbase_client_instance, "get_account"):
                    bal = coinbase_client_instance.get_account()
                elif hasattr(coinbase_client_instance, "get_usd_balance"):
                    bal = coinbase_client_instance.get_usd_balance()
            except Exception as e:
                log.debug("Balance fetch failed (non-fatal): %s", e)
            log.info("Trading loop heartbeat. Balance sample: %s", str(bal)[:300])
        except Exception:
            log.exception("Unexpected error in trading loop")
        await asyncio.sleep(interval)
