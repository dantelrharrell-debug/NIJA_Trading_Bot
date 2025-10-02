# Echo debug handler — paste into main.py, redeploy
from fastapi import FastAPI, Request
from pydantic import BaseModel, ValidationError
from typing import Literal, Optional
import traceback

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
    # Try to read JSON safely
    try:
        raw = await req.json()
    except Exception as e:
        # Return immediate error with exact exception
        return {"status":"error","reason":"invalid_json","detail": str(e)}

    # Return the raw payload back to the caller and also include validation attempts
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
