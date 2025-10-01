from fastapi import FastAPI, Request
import uvicorn
import coinbase_advanced_py as cb

# === Coinbase connection ===
api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"
client = cb.CoinbaseAdvanced(api_key=api_key, api_secret=api_secret)

# === FastAPI setup ===
app = FastAPI()

def calc_trade_size(balance, risk_percent):
    return round(balance * risk_percent, 2)

@app.post("/trade")
async def trade(request: Request):
    data = await request.json()
    symbol = data["symbol"]
    side = data["side"]
    risk_percent = data.get("risk_percent", 0.05)  # default 5%

    # Fetch current price
    price = float(client.get_ticker(symbol)["price"])

    # Fetch current balance (USD only)
    accounts = client.get_accounts()
    balance = float([a['balance'] for a in accounts if a['currency']=="USD"][0])

    trade_amount = calc_trade_size(balance, risk_percent)
    quantity = trade_amount / price

    # Execute order
    order = client.create_order(
        symbol=symbol,
        side=side,
        type="market",
        quantity=quantity
    )
    return {"status": "success", "order": order}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
