import importlib
import importlib.util
import logging
import os
from fastapi import FastAPI, Request

# ---------------- Logging Setup ----------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("all_in_one_bot")

# ---------------- FastAPI App ----------------
app = FastAPI(title="NIJA Trading Bot")

# ---------------- Coinbase Client Auto-Discovery ----------------
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
            CLIENT_MODULE = mod_name + "." + cand_name
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

# ---------------- Root Endpoint ----------------
@app.get("/")
async def root():
    return {
        "status": "Bot is live",
        "coinbase_client_detected": CLIENT_CLASS is not None,
        "coinbase_module": CLIENT_MODULE
    }

# ---------------- Example Webhook Endpoint ----------------
@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    log.info("Received webhook data: %s", data)
    return {"status": "received"}
