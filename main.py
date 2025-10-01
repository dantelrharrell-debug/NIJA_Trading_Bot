# main.py
import os
from fastapi import FastAPI, Request
from pydantic import BaseModel
import coinbase as cb
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "MySuperStrongSecret123!")

# Initialize FastAPI
app = FastAPI()

# Initialize Coinbase client
client = cb.Coinbase(API_KEY, API_SECRET)

# Pydantic model for webhook payload
class WebhookPayload(BaseModel):
    secret: str
    symbol: str
    side: str  # "buy" or "sell"
    risk_percent: float  # e.g., 0.05 for 5% of balance

# Helper function to get USD balance
def get_balance(currency="USD"):
    accounts = client.get_accounts()
    for account in accounts['data']:
        if account['currency'] == currency:
            return float(account['available']['amount'])
    return 0

# Helper function to execute a trade
def execute_trade(symbol, side, amount):
    """
    Placeholder function. Replace with real Coinbase order calls.
    """
    print(f"Executing {side.upper()} trade for {symbol} amount ${amount:.2f}")
    # Example: client.buy(symbol, amount) or client.sell(symbol, amount)
    return True

# Webhook endpoint
@app.post("/webhook")
async def webhook(payload: WebhookPayload):
    if payload.secret != WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    # Calculate trade amount
    balance = get_balance()
    trade_amount = balance * payload.risk_percent

    # Execute trade
    success = execute_trade(payload.symbol, payload.side, trade_amount)
    return {
        "status": "success" if success else "error",
        "symbol": payload.symbol,
        "side": payload.side,
        "trade_amount": trade_amount
    }

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Nija Trading Bot Live!"}
