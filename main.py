# ---- webhook debug handler (paste into your main.py) ----
from fastapi import FastAPI, Request
from pydantic import BaseModel, ValidationError
from typing import Literal, Optional
import traceback

app = FastAPI()

class Order(BaseModel):
    symbol: str                   # "BTC-USD"
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit"]
    amount: float                 # amount in asset units

# legacy / alternate schema (TradingView style)
class LegacyAlert(BaseModel):
    pair: str
    allocation_percent: Optional[float] = None
    price: Optional[float] = None
    time: Optional[str] = None
    strategy: Optional[str] = None  # "buy"/"sell"

@app.post("/webhook")
async def webhook(req: Request):
    try:
        raw = await req.json()
    except Exception as e:
        return {"status": "error", "reason": "invalid_json", "detail": str(e)}

    # Always log raw payload for debugging
    print("RAW WEBHOOK PAYLOAD:", raw)

    # 1) Try strict Order model (symbol/side/order_type/amount)
    try:
        order = Order.parse_obj(raw)
        print("✅ Valid Order schema received:", order.dict())
        # place your real order logic here, or simulate:
        # place_order(order.symbol, order.side, order.order_type, order.amount)
        return {"status": "accepted", "schema": "order", "order": order.dict()}
    except ValidationError as e:
        print("Order schema validation failed:", e.errors())

    # 2) Try legacy schema and convert it to Order-like response
    try:
        legacy = LegacyAlert.parse_obj(raw)
        print("Legacy alert received:", legacy.dict())
        # If legacy has allocation_percent, convert using a placeholder balance calc or return as-is.
        # Example response includes how we'd interpret it (you can adapt to your real logic).
        converted = {
            "pair": legacy.pair,
            "strategy": legacy.strategy,
            "allocation_percent": legacy.allocation_percent,
            "price": legacy.price,
            "note": "Legacy schema received. Convert allocation_percent -> amount in your bot using current USD balance."
        }
        return {"status": "accepted", "schema": "legacy", "converted": converted}
    except ValidationError as e:
        print("Legacy schema validation failed:", e.errors())

    # 3) If we get here: unknown/invalid schema — return a detailed error so the caller can fix it
    return {
        "status": "invalid_order_data",
        "reason": "payload did not match either strict Order schema or LegacyAlert schema",
        "received": raw
    }
