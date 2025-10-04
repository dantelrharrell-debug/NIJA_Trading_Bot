# main.py
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
RENT_DUE_HOURS = float(os.getenv("RENT_DUE_HOURS", "0"))  # if >0 enforce stopping trading within that many hours

# Candidates to try importing for Coinbase Advanced
COINBASE_CANDIDATES = [
    "coinbase_advanced_py",
    "coinbase_advanced",
    "coinbase_advanced_py.client",
    "coinbase_advanced.client",
    "coinbase.wallet",
    "coinbase.wallet.client",
    "coinbase",
]

# Placeholders
CoinbaseClient = None
coinbase_client_instance = None
import_attempts: Dict[str, Dict[str, str]] = {}

def try_import_coinbase():
    global CoinbaseClient, coinbase_client_instance, import_attempts
    import_attempts = {}
    for name in COINBASE_CANDIDATES:
        try:
            spec = importlib.util.find_spec(name)
            if spec is None:
                import_attempts[name] = {"status": "not_found", "detail": "find_spec returned None"}
                continue
            mod = importlib.import_module(name)
            # heuristics to find a client class or Client symbol
            candidate_attrs = ["Client", "client", "CoinbaseClient", "AdvancedClient"]
            found = []
            for a in candidate_attrs:
                if hasattr(mod, a):
                    found.append(a)
            import_attempts[name] = {"status": "imported", "attrs": ",".join(found) or "none"}
            # if we find a Client attr somewhere, use it
            if found:
                CoinbaseClient = getattr(mod, found[0])
                break
            # else if module itself represents the client (rare), store module
            CoinbaseClient = mod
            break
        except Exception as e:
            import_attempts[name] = {"status": "import_failed", "detail": repr(e)}
    return import_attempts

def init_coinbase_client():
    global coinbase_client_instance
    if CoinbaseClient is None:
        return None
    try:
        # many clients accept (api_key, api_secret) or keyword args - try both
        try:
            coinbase_client_instance = CoinbaseClient(API_KEY, API_SECRET)
        except TypeError:
            coinbase_client_instance = CoinbaseClient(api_key=API_KEY, api_secret=API_SECRET)
        log.info("Coinbase client initialized successfully using %s", getattr(CoinbaseClient, "__name__", str(CoinbaseClient)))
        return coinbase_client_instance
    except Exception as e:
        log.exception("Failed to initialize coinbase client: %s", e)
        coinbase_client_instance = None
        return None

# Diagnostics helpers
def list_top_level_modules(limit: int = 200) -> List[str]:
    try:
        return [m.name for m in pkgutil.iter_modules()][:limit]
    except Exception as e:
        return [f"error_listing_modules: {e}"]

def site_packages_paths() -> List[str]:
    import site
    try:
        # On some platforms, getsitepackages may not exist — handle both
        paths = []
        if hasattr(site, "getsitepackages"):
            paths.extend(site.getsitepackages())
        if hasattr(site, "getusersitepackages"):
            paths.append(site.getusersitepackages())
        return paths
    except Exception:
        return []

@app.on_event("startup")
async def startup_event():
    # Print basic environment and attempt import
    log.info("=== NIJA Trading Bot startup ===")
    log.info("python executable: %s", sys.executable)
    log.info("python version: %s", sys.version.splitlines()[0])
    log.info("cwd: %s", os.getcwd())
    log.info("site-packages paths: %s", site_packages_paths())
    log.info("top-level modules sample: %s", list_top_level_modules(80))
    # Try importing Coinbase variants
    try_import_coinbase()
    log.info("coinbase import attempts: %s", import_attempts)
    if any(v.get("status") == "imported" for v in import_attempts.values()):
        init_coinbase_client()
    else:
        log.error("Could not import any Coinbase Advanced module. Bot will continue in diagnostic mode.")
    # If client available and live trading env var true, start background trading loop
    if coinbase_client_instance and LIVE_TRADING:
        # enforce rent guard: if RENT_DUE_HOURS > 0, do not trade when rent is soon
        if RENT_DUE_HOURS > 0:
            log.info("RENT_DUE_HOURS set (%s). Background trading will check time remaining until rent.", RENT_DUE_HOURS)
        log.info("Starting background trading loop (LIVE_TRADING=%s).", LIVE_TRADING)
        asyncio.create_task(trading_loop())

@app.get("/")
async def root():
    return {"status": "ok", "live_trading": LIVE_TRADING, "coinbase": coinbase_client_instance is not None}

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
        "env": {k: os.environ.get(k) for k in ("PORT", "LIVE_TRADING", "RENT_DUE_HOURS")},
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/toggle-live/{state}")
async def toggle_live(state: str):
    """Toggle live trading on/off (state = 'on' or 'off'). Requires redeploy to persist env vars."""
    s = state.lower() in ("1", "on", "true", "yes")
    return {"requested": s, "note": "This endpoint only reports — to persist change set LIVE_TRADING env var or toggle in Render settings."}

# --- Minimal trading loop (VERY small, safe, and easily auditable) ---
async def check_rent_guard() -> bool:
    """
    Return True if trading allowed under rent guard.
    If RENT_DUE_HOURS <= 0, no guard.
    This is a placeholder: you should set RENT_DUE_HOURS to the hours before rent.
    """
    try:
        hours = float(os.getenv("RENT_DUE_HOURS", "0"))
        if hours <= 0:
            return True
        # For now we don't know actual rent due timestamp. Assume user sets RENT_DUE_HOURS
        # If RENT_DUE_HOURS is small, we will block by returning False.
        # This just demonstrates the guard; you must supply a real timestamp in a future enhancement.
        # Here: if RENT_DUE_HOURS < 1 -> block trading for safety.
        if hours < 1.0:
            log.warning("RENT_DUE_HOURS < 1, blocking live trading as safety measure.")
            return False
        return True
    except Exception as e:
        log.exception("Rent guard check failed: %s", e)
        return False

async def trading_loop():
    """
    Very small autonomous loop:
    - polls account info every 10s (configurable)
    - applies a trivial strategy placeholder
    - places no real orders by default unless you implement place_order()
    """
    interval = int(os.getenv("TRADING_POLL_INTERVAL", "10"))
    log.info("Trading loop started with poll interval %s seconds", interval)
    while True:
        try:
            # rent guard
            if not await check_rent_guard():
                log.info("Rent guard blocked trading. Sleeping and re-checking.")
                await asyncio.sleep(30)
                continue

            if not coinbase_client_instance:
                log.error("No coinbase client instance available; trading loop exiting.")
                return

            # Example: fetch a small diagnostic of balances (method name differs by client)
            bal = None
            try:
                # many clients have methods like 'get_account' or 'get_balance' — this is best-effort
                if hasattr(coinbase_client_instance, "get_accounts"):
                    bal = coinbase_client_instance.get_accounts()
                elif hasattr(coinbase_client_instance, "get_account"):
                    bal = coinbase_client_instance.get_account()
                elif hasattr(coinbase_client_instance, "get_usd_balance"):
                    bal = coinbase_client_instance.get_usd_balance()
                else:
                    bal = "no_balance_method_found"
            except Exception as e:
                log.debug("Balance fetch failed (non-fatal): %s", e)

            log.info("Trading loop heartbeat. Balance sample: %s", str(bal)[:300])

            # Placeholder strategy: do nothing. If you want to place orders, implement place_order below.
            # If you want aggressive 'trade everything' behavior, edit place_order carefully.
            # Example usage (commented): await place_order(symbol='BTC-USD', side='buy', size=0.001)

        except Exception as e:
            log.exception("Unexpected error in trading loop: %s", e)
        await asyncio.sleep(interval)

async def place_order(symbol: str, side: str, size: float):
    """
    Very small wrapper to place an order. This is NOT called anywhere by default.
    Use with caution. Must match your client API.
    """
    if not coinbase_client_instance:
        raise RuntimeError("Coinbase client not initialized.")
    log.info("Placing order (TEST WRAPPER) symbol=%s side=%s size=%s", symbol, side, size)
    # Example (pseudocode) — the real method name depends on the client
    try:
        if hasattr(coinbase_client_instance, "create_order"):
            resp = coinbase_client_instance.create_order(product_id=symbol, side=side, size=size)
            log.info("Order response: %s", resp)
            return resp
        elif hasattr(coinbase_client_instance, "place_order"):
            resp = coinbase_client_instance.place_order(symbol=symbol, side=side, size=size)
            log.info("Order response: %s", resp)
            return resp
        else:
            raise RuntimeError("No order method known on client")
    except Exception:
        log.exception("Order failed")
        raise
