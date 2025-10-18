# webhook_handler.py
import os
import hmac
import hashlib
import json
import logging
import uuid
from fastapi import APIRouter, Request, Header, HTTPException
from starlette.responses import JSONResponse

router = APIRouter()
logger = logging.getLogger("nija")

# env vars
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
DRY_RUN = os.getenv("DRY_RUN", "true").lower() in ("1","true","yes")

def compute_hmac_sha256(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

@router.post("/webhook")
async def tradingview_webhook(
    request: Request,
    x_signature: str | None = Header(None),        # adapt header name used by your alarms
    x_request_id: str | None = Header(None),
):
    req_id = x_request_id or str(uuid.uuid4())
    raw_body = await request.body()

    # OPTIONAL: log receipt (truncated)
    logger.info({"evt":"webhook.received", "req_id": req_id, "body_preview": raw_body.decode("utf-8", errors="replace")[:1000]})

    # 1) HMAC verification if secret provided
    if WEBHOOK_SECRET:
        if not x_signature:
            logger.warning({"evt":"webhook.no_signature","req_id":req_id})
            raise HTTPException(status_code=401, detail="Missing signature header")

        expected = compute_hmac_sha256(WEBHOOK_SECRET, raw_body)
        # try tolerant compare (hex lowercase)
        if not hmac.compare_digest(expected, x_signature.lower()):
            logger.warning({"evt":"webhook.bad_signature","req_id":req_id, "expected": expected, "got": x_signature})
            raise HTTPException(status_code=401, detail="Invalid signature")

    # 2) Safe JSON parse
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        logger.error({
            "evt":"webhook.json_decode_error",
            "req_id": req_id,
            "error": str(e),
            "raw_preview": raw_body.decode("utf-8", errors="replace")[:4000],
        })
        raise HTTPException(status_code=400, detail="Invalid JSON")

    logger.info({"evt":"webhook.parsed","req_id":req_id,"payload_preview": {k: payload.get(k) for k in ("ticker","symbol","side","size","passphrase") if k in payload}})

    # 3) Basic payload validation (adapt keys to your TradingView message)
    # Accept either "symbol" or "ticker" for compatibility
    symbol = payload.get("symbol") or payload.get("ticker")
    side = (payload.get("side") or "").lower()
    size = payload.get("size") or payload.get("qty") or payload.get("quantity")
    passphrase = payload.get("passphrase")  # if you use one

    if not symbol or side not in ("buy","sell") or not size:
        logger.warning({"evt":"webhook.invalid_payload","req_id":req_id,"symbol":symbol,"side":side,"size":size})
        raise HTTPException(status_code=422, detail="Missing or invalid fields")

    # 4) Dry-run safety
    order_payload = {
        "symbol": symbol,
        "side": side,
        "size": size,
        "meta": {
            "req_id": req_id,
            "source": "tradingview"
        }
    }

    if DRY_RUN:
        logger.info({"evt":"order.dry_run","req_id":req_id,"order": order_payload})
        return JSONResponse({"status":"dry_run", "req_id": req_id, "order": order_payload})

    # 5) Place order (replace with your actual function that calls Coinbase SDK)
    try:
        # Example: result = place_order_on_coinbase(order_payload)
        # Replace the next line with your live call
        logger.info({"evt":"order.sending","req_id":req_id,"order":order_payload})
        result = {"ok": True, "order_id": "SIM-12345"}  # placeholder
        logger.info({"evt":"order.sent","req_id":req_id,"result": result})
    except Exception as e:
        logger.exception({"evt":"order.error","req_id":req_id,"error": str(e)})
        raise HTTPException(status_code=500, detail="Order placement failed")

    return JSONResponse({"status":"ok","req_id":req_id,"result": result})
