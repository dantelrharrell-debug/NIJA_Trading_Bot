# Echo debug handler — paste into main.py and redeploy
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Literal, Optional
import json

app = FastAPI()

class Order(BaseModel):
    symbol: str
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit"]
    amount: float

class LegacyAlert(BaseModel):
    pair: str
    allocation_percent: Optional[float] = None
    price: Optional[float] = None
    time: Optional[str] = None
    strategy: Optional[str] = None

@app.post("/webhook")
async def webhook(req: Request):
    # read body
    try:
        raw = await req.json()
    except Exception as e:
        # If body is plain text or stringified JSON, return the raw text too
        text = await req.body()
        return {"status": "invalid_json", "error": str(e), "raw_text": text.decode(errors="replace")}

    # Try to parse nested stringified JSON automatically (common case)
    if isinstance(raw, str):
        try:
            raw_parsed = json.loads(raw)
            raw = raw_parsed
        except Exception:
            pass

    # Return what we received and simple validation results
    result = {"raw_received": raw, "validation": {}}

    # Try strict schema
    try:
        order = Order.parse_obj(raw)
        result["validation"]["order"] = {"ok": True, "order": order.dict()}
    except Exception as e:
        result["validation"]["order"] = {"ok": False, "error": str(e)}

    # Try legacy schema
    try:
        legacy = LegacyAlert.parse_obj(raw)
        result["validation"]["legacy"] = {"ok": True, "legacy": legacy.dict()}
    except Exception as e:
        result["validation"]["legacy"] = {"ok": False, "error": str(e)}

    return result
