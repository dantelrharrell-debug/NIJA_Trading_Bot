from fastapi import FastAPI, Request
import uvicorn
import coinbase_advanced_py as cb

# === Coinbase connection ===
API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"
client = cb.CoinbaseAdvanced(api_key=API_KEY, api_secret=API_SECRET)

# === FastAPI setup ===
app = FastAPI()

# === Risk settings ===
MIN_RISK = 0.02
MAX_RISK = 0.10

# Optional security key for webhook validation
WEBHOOK_SECRET = "YOUR_SECRET_KEY"

# === Trade size calculation ===
def calc_trade_size(balance, risk_percent):
    # Clamp risk percent to min/max
    risk_percent = max(MIN_RISK, min(MAX_RISK, risk_percent))
    return round(balance * risk_percent, 2)

# === Trade endpoint for TradingView webhooks ===
@app.post("/trade")
async def trade(request: Request):
    data = await request.json()
    
    # Security check
    if data.get("secret") != WEBHOOK_SECRET:
        return {"status": "error", "message": "Unauthorized"}

    try:
        symbol = data["symbol"]  # e.g., "BTC-USD"
        side = data["side"].lower()  # "buy" or "sell"
        risk_percent = float(data.get("risk_percent", 0.05))  # default 5%
    except Exception as e:
        return {"status": "error", "message": f"Invalid payload: {e}"}

    # Get current USD balance
    accounts = client.get_accounts()
    usd_balance = float([a['balance'] for a in accounts if a['currency'] == "USD"][0])

    # Calculate trade amount & quantity
    trade_amount = calc_trade_size(usd_balance, risk_percent)
    
    # Fetch current price
    price = float(client.get_ticker(symbol)["price"])
    quantity = round(trade_amount / price, 8)  # precision safe for Coinbase

    if quantity < 0.0001:  # Coinbase minimum trade size safety check
        return {"status": "error", "message": "Trade below minimum size"}

    # Execute market order
    order = client.create_order(
        symbol=symbol,
        side=side,
        type="market",
        quantity=quantity
    )

    return {
        "status": "success",
        "symbol": symbol,
        "side": side,
        "risk_percent": risk_percent,
        "trade_amount": trade_amount,
        "quantity": quantity,
        "price": price,
        "order": order
    }

# === Run bot ===
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
