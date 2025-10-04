from fastapi import FastAPI, Request
from coinbase_advanced_py import Client
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TRADINGVIEW_SECRET = os.getenv("TRADINGVIEW_SECRET")

client = Client(API_KEY, API_SECRET)

app = FastAPI()

@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()

    if TRADINGVIEW_SECRET and data.get("secret") != TRADINGVIEW_SECRET:
        return {"status": "error", "message": "Unauthorized"}

    symbol = data.get("symbol", "BTC-USD")
    side = data.get("side", "buy")
    size = float(data.get("size", 0.001))

    order = client.place_order(
        product_id=symbol,
        side=side,
        type="market",
        size=size
    )
    return {"status": "success", "order": order}
