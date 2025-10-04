# main.py (example)
import logging
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from coinbase_loader import get_coinbase_client, get_coinbase_client_class

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="NIJA Trading Bot - diagnostic")

# Try to get a client instance (safe)
client_instance, client_identifier, client_error = get_coinbase_client()

if client_instance:
    log.info("Coinbase client ready: %s", client_identifier)
else:
    if client_identifier is None:
        log.warning("Coinbase client NOT FOUND. Running in diagnostic mode. Error: %s", client_error)
    else:
        log.error("Coinbase client module found (%s) but failed to instantiate: %s", client_identifier, client_error)

@app.get("/")
async def root():
    return {"status": "ok", "coinbase_client": bool(client_instance), "client_id": client_identifier}

@app.get("/diag")
async def diag():
    # Give helpful diagnostic info the logs showed
    return JSONResponse({
        "coinbase_client_available": bool(client_instance),
        "client_identifier": client_identifier,
        "instantiation_error": repr(client_error) if client_error else None,
        "env": {
            "COINBASE_API_KEY": bool(os.environ.get("COINBASE_API_KEY")),
            "COINBASE_API_SECRET": bool(os.environ.get("COINBASE_API_SECRET")),
            "COINBASE_API_PASSPHRASE": bool(os.environ.get("COINBASE_API_PASSPHRASE")),
        }
    })

# Example safe order function: DO NOT run unless client_instance is non-None and you've reviewed it.
@app.post("/place_test_order")
async def place_test_order():
    if not client_instance:
        return JSONResponse({"error": "no coinbase client available"}, status_code=500)
    # WARNING: different client libraries have different APIs. This is only pseudocode:
    try:
        if hasattr(client_instance, "create_order"):
            # coinbase-advanced-py style? You must adapt these fields to the library you use.
            resp = client_instance.create_order(product_id="BTC-USD", side="buy", size="0.0001", type="market")
            return {"result": "order_sent", "response": repr(resp)}
        elif hasattr(client_instance, "buy") or hasattr(client_instance, "sell"):
            # fallback: common names
            if hasattr(client_instance, "buy"):
                resp = client_instance.buy(amount="1", currency="USD")
            else:
                resp = client_instance.sell(amount="1", currency="USD")
            return {"result": "order_sent", "response": repr(resp)}
        else:
            return {"error": "client present but API shape unknown; adapt code"}
    except Exception as e:
        log.exception("Order attempt failed")
        return JSONResponse({"error": repr(e)}, status_code=500)
