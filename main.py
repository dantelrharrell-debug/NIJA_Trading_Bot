# main.py (updated)

# ... previous imports ...
from coinbase.wallet.client import Client
import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "MySuperStrongSecret123!")

app = FastAPI()
client = Client(API_KEY, API_SECRET)

# Minimum trade amounts (Coinbase defaults, adjust if needed)
MIN_TRADE_USD = 1.0  # Minimum $1 per trade
MIN_TRADE_BTC = 0.0001  # Example for BTC, adjust per asset

class WebhookPayload(BaseModel):
    secret: str
    symbol: str
    side: str  # "buy" or "sell"
    risk_percent: float  # e.g., 0.05 for 5% of balance

def get_balance(currency="USD"):
    accounts = client.get_accounts()
    for account in accounts.data:
        if account.currency == currency:
            return float(account.balance.amount)
    return 0

# Updated execute_trade with minimum trade check
def execute_trade(symbol, side, amount):
    # Check minimum for USD
    if symbol.upper() == "USD" and amount < MIN_TRADE_USD:
        print(f"Trade amount ${amount:.2f} is below the minimum ${MIN_TRADE_USD}. Skipping trade.")
        return False

    # Example: for BTC or other crypto
    if symbol.upper() == "BTC" and amount < MIN_TRADE_BTC:
        print(f"Trade amount {amount:.6f} BTC is below minimum {MIN_TRADE_BTC} BTC. Skipping trade.")
        return False

    print(f"Executing {side.upper()} trade for {symbol} amount ${amount:.2f}")
    # Use real API call here: client.buy(...) or client.sell(...)
    return True

@app.post("/webhook")
async def webhook(payload: WebhookPayload):
    if payload.secret != WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    balance = get_balance()
    trade_amount = balance * payload.risk_percent
    success = execute_trade(payload.symbol, payload.side, trade_amount)

    return {
        "status": "success" if success else "skipped",
        "symbol": payload.symbol,
        "side": payload.side,
        "trade_amount": trade_amount
    }

@app.get("/")
async def root():
    return {"message": "Nija Trading Bot Live!"}
