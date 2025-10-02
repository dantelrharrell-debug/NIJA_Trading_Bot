from fastapi import FastAPI, Request, HTTPException
import os
from coinbase_advanced_py import CoinbaseAdvanced

app = FastAPI()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "MySuperStrongSecret123!")
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET")

if not COINBASE_API_KEY or not COINBASE_API_SECRET:
    raise ValueError("Coinbase API key and secret must be set")

client = CoinbaseAdvanced(api_key=COINBASE_API_KEY, api_secret=COINBASE_API_SECRET)

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    if data.get("secret") != WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    symbol = data.get("symbol")
    side = data.get("side")
    risk_percent = float(data.get("risk_percent"))

    if not symbol or not side or risk_percent is None:
        raise HTTPException(status_code=400, detail="Missing trade data")

    # Execute trade
    account = client.get_account(symbol)
    available_balance = float(account['available'])
    trade_size = available_balance * risk_percent

    order = client.create_order(
        product_id=symbol,
        side=side.lower(),
        type="market",
        size=str(trade_size)
    )

    return {"status": "ok", "message": f"{side.upper()} {symbol} executed for {trade_size}"}
