import os
from dotenv import load_dotenv
load_dotenv()

try:
    from coinbase_advanced_py import Client
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "coinbase_advanced_py not found. Ensure requirements.txt has coinbase-advanced-py==1.8.2"
    )

from fastapi import FastAPI, Request
import numpy as np

# FastAPI app
app = FastAPI(title="NIJA Trading Bot")

# Coinbase client
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
cb_client = Client(API_KEY, API_SECRET)

@app.get("/")
async def root():
    return {"status": "NIJA Trading Bot Online"}

@app.post("/webhook")
async def webhook_listener(request: Request):
    """Receive TradingView webhook signals."""
    data = await request.json()
    secret = data.get("secret")
    if secret != os.getenv("WEBHOOK_SECRET"):
        return {"status": "Unauthorized"}

    symbol = data.get("symbol")
    action = data.get("action")  # "buy" or "sell"

    # Example: placeholder for executing trade
    print(f"Webhook received: {symbol} -> {action}")
    
    return {"status": "Webhook received", "symbol": symbol, "action": action}
