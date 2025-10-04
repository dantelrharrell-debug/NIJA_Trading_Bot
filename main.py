# main.py
import os
import json
from fastapi import FastAPI, Request, HTTPException
from coinbase_advanced_py import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise ValueError("API_KEY and API_SECRET must be set in .env")

# Initialize Coinbase Advanced client
client = Client(API_KEY, API_SECRET)

# Initialize FastAPI app
app = FastAPI(title="NIJA Trading Bot Webhook")

# Root route to check if service is live
@app.get("/")
async def root():
    return {"status": "NIJA Trading Bot is live"}

# Webhook route
@app.post("/webhook")
async def webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Example expected payload:
    # {
    #   "symbol": "BTC-USD",
    #   "side": "buy",
    #   "type": "market",
    #   "size": 0.001
    # }

    symbol = payload.get("symbol")
    side = payload.get("side")
    order_type = payload.get("type", "market")
    size = payload.get("size")

    if not all([symbol, side, size]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        order = client.create_order(
            product_id=symbol,
            side=side,
            order_type=order_type,
            size=size
        )
        return {"status": "success", "order": order}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Optional: route to check account balances
@app.get("/balances")
async def balances():
    try:
        accounts = client.get_accounts()
        balances = {acct['currency']: acct['balance'] for acct in accounts}
        return {"status": "success", "balances": balances}
    except Exception as e:
        return {"status": "error", "message": str(e)}
