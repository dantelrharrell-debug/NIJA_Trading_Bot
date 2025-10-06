import os
import coinbase_advanced_py as cb

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set")

client = cb.Client(API_KEY, API_SECRET)

print("🚀 Trading bot started")

# Example: check balances
balances = client.get_account_balances()
print(balances)
import os
from pyngrok import ngrok

# Load the token from Replit secrets
NGROK_TOKEN = os.getenv("NGROK_TOKEN")
if not NGROK_TOKEN:
    raise ValueError("❌ NGROK_TOKEN not set in Replit secrets!")

# Set the auth token for pyngrok
ngrok.set_auth_token(NGROK_TOKEN)

# Start a tunnel on your bot's port (replace 5000 if needed)
public_url = ngrok.connect(5000)
print(f"🚀 ngrok tunnel running at {public_url}")
# main.py
import os
import asyncio
import logging
from fastapi import FastAPI

# ---- config ----
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SEC", "30"))  # how often to poll balances
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

# ---- logging ----
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("nija")

# ---- try to initialize a Coinbase client (try modern, fallback to classic) ----
client = None
client_type = None

try:
    import coinbase_advanced_py as cbadv
    # constructor may vary; adapt if your version differs
    client = cbadv.Client(API_KEY, API_SECRET)
    client_type = "coinbase_advanced_py"
    logger.info("Using coinbase_advanced_py client")
except Exception as e_adv:
    logger.info("coinbase_advanced_py not usable, trying coinbase.wallet.client: %s", e_adv)
    try:
        from coinbase.wallet.client import Client as CBWalletClient
        client = CBWalletClient(API_KEY, API_SECRET)
        client_type = "coinbase_wallet_client"
        logger.info("Using coinbase.wallet.client")
    except Exception as e_legacy:
        logger.exception("No Coinbase client available: %s", e_legacy)
        client = None

# ---- helper: safe call for balances ----
def safe_get_balances():
    """Try a few common SDK methods to fetch balances; return dict or string on error."""
    if client is None:
        return {"error": "no_client"}
    try:
        # Try common modern name
        if hasattr(client, "get_account_balances"):
            return client.get_account_balances()
        # common fallback: list/get accounts
        if hasattr(client, "get_accounts"):
            return client.get_accounts()
        if hasattr(client, "get_accounts_list"):
            return client.get_accounts_list()
        # coinbase.wallet.client: may have get_accounts() returning list-like
        if hasattr(client, "get_account"):
            # we don't know the account id; return generic string
            return {"info": "client has get_account but requires account id"}
        return {"error": "no_known_balance_method"}
    except Exception as e:
        logger.exception("Error fetching balances: %s", e)
        return {"error": str(e)}

# ---- order placement helper (safe: respects DRY_RUN) ----
def place_order_safe(order_payload: dict):
    """
    Log order payload and, if DRY_RUN is false AND you have a working SDK method,
    send the order. This function intentionally does not call any concrete
    SDK order method by default — adapt with caution.
    """
    logger.info("place_order_safe called: DRY_RUN=%s payload=%s", DRY_RUN, order_payload)
    if DRY_RUN:
        return {"status": "dry_run", "payload": order_payload}

    # ======= DANGER ZONE =======
    # If you really want to place a live order, insert your SDK call here after testing.
    # Example (pseudocode):
    # if client_type == "coinbase_wallet_client":
    #     acct = client.get_account("BTC-USD")  # note: likely not valid — adapt to real account ID
    #     res = acct.buy(amount=..., currency="USD")
    # elif client_type == "coinbase_advanced_py":
    #     res = client.place_order(...)
    # return res
    raise RuntimeError("Live order placement is not implemented. Set DRY_RUN=false and implement SDK call with care.")

# ---- background polling task (non-blocking) ----
app = FastAPI()

async def balance_poller():
    logger.info("Balance poller started. interval=%s", POLL_INTERVAL)
    while True:
        try:
            balances = safe_get_balances()
            logger.info("Balances poll result: %s", str(balances)[:2000])
        except Exception as e:
            logger.exception("Exception in balance_poller: %s", e)
        await asyncio.sleep(POLL_INTERVAL)

@app.on_event("startup")
async def startup_event():
    # start background task but don't await (Fire-and-forget)
    asyncio.create_task(balance_poller())
    logger.info("App startup complete. DRY_RUN=%s WEBHOOK_SECRET_SET=%s", DRY_RUN, bool(WEBHOOK_SECRET))

# ---- include webhook router if you have it ----
try:
    from webhook_handler import router as webhook_router
    app.include_router(webhook_router)
    logger.info("Webhook router included.")
except Exception as e:
    logger.warning("webhook_handler import failed: %s", e)

# ---- simple health endpoint ----
@app.get("/health")
async def health():
    return {"status": "ok", "client": client_type, "dry_run": DRY_RUN}
