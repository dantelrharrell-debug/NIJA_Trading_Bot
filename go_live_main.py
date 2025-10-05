# go_live_main.py
import os
import asyncio
import logging
import traceback
from fastapi import FastAPI, Header, HTTPException, Body
from fastapi.responses import JSONResponse

# ----------------------
# Configuration (env)
# ----------------------
# You asked to "start trading go live" — DRY_RUN defaults to False here.
DRY_RUN = os.getenv("DRY_RUN", "false").lower() in ("1", "true", "yes")
# Extra safety: live order execution requires this to be explicitly set to "true".
LIVE_ORDER_ENABLED = os.getenv("LIVE_ORDER_ENABLED", "false").lower() in ("1", "true", "yes")
# Kill switch (set to "ON" to block all orders immediately)
KILL_SWITCH = os.getenv("KILL_SWITCH", "OFF").upper()
# Per-order USD cap to avoid giant accidental orders
MAX_ORDER_USD = float(os.getenv("MAX_ORDER_USD", "10"))
# Admin secret (protect admin endpoints)
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "change-me")
# Polling interval for balances
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SEC", "30"))

# ----------------------
# Logging
# ----------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("nija")

# ----------------------
# Initialize Coinbase client (try modern SDK, fallback to legacy)
# ----------------------
client = None
client_type = None
try:
    import coinbase_advanced_py as cbadv
    client = cbadv.Client(os.getenv("API_KEY"), os.getenv("API_SECRET"))
    client_type = "coinbase_advanced_py"
    logger.info("Using coinbase_advanced_py client")
except Exception as e:
    logger.info("coinbase_advanced_py not available or failed to init: %s", e)
    try:
        from coinbase.wallet.client import Client as CBWalletClient
        client = CBWalletClient(os.getenv("API_KEY"), os.getenv("API_SECRET"))
        client_type = "coinbase_wallet_client"
        logger.info("Using coinbase.wallet.client")
    except Exception as e2:
        logger.warning("No Coinbase client available: %s", e2)
        client = None

# ----------------------
# Helper functions
# ----------------------
def can_place_order(usd_value_estimate: float):
    """Return (ok:bool, reason:str|None)"""
    if os.getenv("KILL_SWITCH", KILL_SWITCH).upper() == "ON":
        return False, "kill_switch"
    if usd_value_estimate > float(os.getenv("MAX_ORDER_USD", MAX_ORDER_USD)):
        return False, "max_order_exceeded"
    return True, None

def place_order_safe(order_payload: dict, usd_value_estimate: float):
    """
    Centralized order gate:
      - If KILL_SWITCH is ON -> block
      - If exceeds MAX_ORDER_USD -> block
      - If DRY_RUN -> returns dry_run
      - If LIVE_ORDER_ENABLED is False -> returns blocked_by_live_flag
      - If client is available and LIVE_ORDER_ENABLED True -> attempt to place order
    IMPORTANT: adapt SDK call below to the exact method of your installed SDK.
    """
    logger.info("place_order_safe called: DRY_RUN=%s LIVE_ORDER_ENABLED=%s payload=%s",
                DRY_RUN, LIVE_ORDER_ENABLED, order_payload)

    ok, reason = can_place_order(usd_value_estimate)
    if not ok:
        logger.warning("Order blocked: %s payload=%s", reason, order_payload)
        return {"status": "blocked", "reason": reason}

    if DRY_RUN:
        logger.info("DRY_RUN active — not sending live order. payload=%s", order_payload)
        return {"status": "dry_run", "order": order_payload}

    if not LIVE_ORDER_ENABLED:
        logger.warning("LIVE_ORDER_ENABLED is false — refusing to send live order.")
        return {"status": "blocked", "reason": "live_flag_disabled"}

    if client is None:
        logger.error("No exchange client available to send order.")
        return {"status": "error", "reason": "no_client"}

    # -----------------------
    # LIVE ORDER: adapt SDK call here carefully
    # -----------------------
    try:
        # Example pseudo-implementation — **YOU MUST ADAPT** to the real SDK API
        # For coinbase_advanced_py, replace with their documented place_order method.
        # For coinbase.wallet.client, you likely need an account id and call account.buy/sell with amount+currency.
        if client_type == "coinbase_advanced_py":
            # PSEUDO: adjust fields for the real method signature
            result = client.place_market_order(
                symbol=order_payload.get("symbol"),
                side=order_payload.get("side"),
                quantity=order_payload.get("size"),
            )
        elif client_type == "coinbase_wallet_client":
            # PSEUDO: the wallet client usually requires account id; this is illustrative only
            # find account and place order via account.buy / account.sell
            account_id = order_payload.get("account_id")  # placeholder
            if not account_id:
                raise RuntimeError("Missing account_id for legacy client")
            acct = client.get_account(account_id)
            if order_payload.get("side") == "buy":
                result = acct.buy(amount=str(order_payload.get("size")), currency="USD")
            else:
                result = acct.sell(amount=str(order_payload.get("size")), currency="USD")
        else:
            raise RuntimeError("Unsupported client_type: %s" % client_type)

        logger.info("Live order result: %s", str(result))
        return {"status": "sent", "result": result}
    except Exception as e:
        logger.exception("Exception placing live order: %s", e)
        return {"status": "error", "reason": str(e)}

# ----------------------
# FastAPI app + background poller
# ----------------------
app = FastAPI()

async def balance_poller():
    logger.info("Balance poller starting. interval=%s", POLL_INTERVAL)
    while True:
        try:
            if client is None:
                logger.warning("No client: skipping balance poll")
            else:
                # try a few common methods to fetch balances
                try:
                    if hasattr(client, "get_account_balances"):
                        b = client.get_account_balances()
                    elif hasattr(client, "get_accounts"):
                        b = client.get_accounts()
                    else:
                        b = {"info":"unknown_balance_method_on_client"}
                    logger.info("Balances: %s", str(b)[:2000])
                except Exception as be:
                    logger.exception("Error during balance fetch: %s", be)
        except Exception as e:
            logger.exception("Balance poller top-level error: %s", e)
        await asyncio.sleep(POLL_INTERVAL)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(balance_poller())
    logger.info("app startup complete DRY_RUN=%s LIVE_ORDER_ENABLED=%s KILL_SWITCH=%s MAX_ORDER_USD=%s",
                DRY_RUN, LIVE_ORDER_ENABLED, os.getenv("KILL_SWITCH", KILL_SWITCH), MAX_ORDER_USD)

# ----------------------
# Include your webhook router (if present)
# ----------------------
try:
    from webhook_handler import router as webhook_router
    app.include_router(webhook_router)
    logger.info("Included webhook_handler router.")
except Exception as e:
    logger.warning("Could not include webhook_handler: %s", e)

# ----------------------
# Admin endpoints (protected by ADMIN_SECRET)
# ----------------------
def check_admin_secret(x_admin_secret: str | None):
    if x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=401, detail="unauthorized")

@app.post("/admin/kill")
async def admin_kill(action: str = Body(..., embed=True), x_admin_secret: str | None = Header(None)):
    """
    Toggle kill switch. action = "on" or "off".
    """
    check_admin_secret(x_admin_secret)
    if action.lower() == "on":
        os.environ["KILL_SWITCH"] = "ON"
    else:
        os.environ["KILL_SWITCH"] = "OFF"
    return {"kill_switch": os.environ["KILL_SWITCH"]}

@app.post("/admin/live_enable")
async def admin_live_enable(action: str = Body(..., embed=True), x_admin_secret: str | None = Header(None)):
    """
    Toggle live-order execution flag. action = "enable" or "disable".
    This is the extra guard that prevents accidental live orders.
    """
    check_admin_secret(x_admin_secret)
    if action.lower() in ("enable","on","true"):
        os.environ["LIVE_ORDER_ENABLED"] = "true"
    else:
        os.environ["LIVE_ORDER_ENABLED"] = "false"
    return {"live_order_enabled": os.environ["LIVE_ORDER_ENABLED"]}

@app.post("/admin/set_max_order_usd")
async def admin_set_max_order_usd(value: float = Body(..., embed=True), x_admin_secret: str | None = Header(None)):
    check_admin_secret(x_admin_secret)
    os.environ["MAX_ORDER_USD"] = str(value)
    return {"MAX_ORDER_USD": os.environ["MAX_ORDER_USD"]}

# ----------------------
# Health (and basic order endpoint for manual testing)
# ----------------------
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "client": client_type,
        "dry_run": DRY_RUN,
        "live_order_enabled": os.getenv("LIVE_ORDER_ENABLED", str(LIVE_ORDER_ENABLED)),
        "kill_switch": os.getenv("KILL_SWITCH", KILL_SWITCH),
    }

@app.post("/manual_order")
async def manual_order(symbol: str = Body(...), side: str = Body(...), size: float = Body(...)):
    """
    Manual order endpoint for quick manual tests (protected by KILL_SWITCH and LIVE flags).
    Note: do NOT expose to the public without additional auth.
    """
    order = {"symbol": symbol, "side": side, "size": size}
    # estimate USD value conservatively: you should compute market price properly
    usd_estimate = float(os.getenv("MAX_ORDER_USD", MAX_ORDER_USD))  # placeholder
    res = place_order_safe(order, usd_estimate)
    return JSONResponse(res)
