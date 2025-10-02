# DEBUG webhook handler — paste into main.py (replaces previous /webhook)
from fastapi import FastAPI, Request
from pydantic import BaseModel, ValidationError
from typing import Literal, Optional

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
    try:
        raw = await req.json()
    except Exception as e:
        print("RAW WEBHOOK PAYLOAD: <invalid json>", str(e))
        return {"status":"error","reason":"invalid_json","detail":str(e)}

    # <- COPY THE RAW PAYLOAD FROM RENDER LOGS (this line prints it)
    print("RAW WEBHOOK PAYLOAD:", raw)

    # try strict schema
    try:
        order = Order.parse_obj(raw)
        print("✅ Valid Order schema received:", order.dict())
        return {"status":"accepted","schema":"order","order":order.dict()}
    except ValidationError as e:
        print("Order schema validation failed:", e.errors())

    # try legacy schema
    try:
        legacy = LegacyAlert.parse_obj(raw)
        print("Legacy alert received:", legacy.dict())
        return {"status":"accepted","schema":"legacy","converted":legacy.dict()}
    except ValidationError as e:
        print("Legacy schema validation failed:", e.errors())

    return {"status":"invalid_order_data","received":raw}
