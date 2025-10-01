# main.py - Fully Live-Trading Ready Nija Bot

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

class WebhookPayload(BaseModel):
    secret: str
    symbol: str        # e.g., "BTC-USD"
    side: str          # "buy" or "sell"
    risk_percent: float  # e.g., 0.05 for 5% of balance

def get_balance(currency):
    """Get account balance for the given currency"""
    accounts = client.get_accounts()
    for account in accounts.data:
        if account.currency == currency:
            return float(account.balance.amount)
    return 0

def get_min_trade(symbol):
    """Fetch minimum trade size for the given trading pair"""
    try:
        product = client.get_product(symbol)
        min_size = float(product['base_min_size'])
        return min_size
    except Exception as e:
        print(f"Error fetching min trade for {symbol}: {e}")
        return 0.0001  # safe fallback

def round_to_precision(amount, symbol):
    """Round trade amount to Coinbase precision"""
    try:
        product = client.get_product(symbol)
        precision = float(product['base_increment'])
        rounded = round(amount // precision * precision, 8)
        return rounded
    except Exception as e:
        print(f"Error rounding amount for {symbol}: {e}")
        return amount

def execute_trade(symbol, side, amount):
    """Execute real buy/sell orders"""
    min_trade = get_min_trade(symbol)
    if amount < min_trade:
        print(f"[SKIP] Trade amount {amount} below minimum {min_trade} for {symbol}")
        return False

    amount = round_to_precision(amount, symbol)
    print(f"[EXECUTE] {side.upper()} {symbol} amount: {amount}")

    try:
        if side.lower() == "buy":
            order = client.buy(symbol=symbol, size=str(amount))
        else:
            order = client.sell(symbol=symbol, size=str(amount))
        print(f"[SUCCESS] Order executed: {order}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to execute {side} for {symbol}: {e}")
        return False

@app.post("/webhook")
async def webhook(payload: WebhookPayload):
    if payload.secret != WEBHOOK_SECRET:
        return {"status": "error", "message": "Invalid secret"}

    base_currency, quote_currency = payload.symbol.split("-")

    if payload.side.lower() == "buy":
        balance = get_balance(quote_currency)
        trade_amount = balance * payload.risk_percent
        trade_amount = trade_amount / get_min_trade(payload.symbol) * get_min_trade(payload.symbol)
    else:
        balance = get_balance(base_currency)
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
