# main.py
from fastapi import FastAPI, Request
import uvicorn
import coinbase_advanced_py as cb

# === Coinbase API Keys ===
API_KEY = "f0e7ae67-cf8a-4aee-b3cd-17227a1b8267"
API_SECRET = "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49"

client = cb.CoinbaseAdvanced(api_key=API_KEY, api_secret=API_SECRET)

# === Webhook secret for TradingView security ===
WEBHOOK_SECRET = "MySuperStrongSecret123!"

# === Risk settings ===
MIN_RISK = 0.02  # 2%
MAX_RISK = 0.10  # 10%

# === FastAPI setup ===
app = FastAPI()

# === Trade size calculation ===
def calc_trade_size(balance, risk_percent):
    # Clamp risk percent to min/max
    risk_percent = max(MIN_RISK, min(MAX_RISK, risk_percent))
    return round(balance * risk_percent, 2)

# === TradingView webhook endpoint ===
@app.post("/webhook")
async def trade(request: Request):
    data = await request.json()

    # Validate webhook secret
    if data.get("secret") != WEBHOOK_SECRET:
        return {"status": "error", "message": "Unauthorized"}

    try:
        symbol = data["symbol"]  # e.g., "BTC-USD"
        side = data["side"].lower()  # "buy" or "sell"
        risk_percent = float(data.get("risk_percent", 0.05))  # default 5%
    except Exception as e:
        return {"status": "error", "message": f"Invalid payload: {e}"}

    # Get USD balance
    accounts = client.get_accounts()
    usd_balance = float([a['balance'] for a in accounts if a['currency'] == "USD"][0])

    # Calculate trade amount and quantity
    trade_amount = calc_trade_size(usd_balance, risk_percent)
    price = float(client.get_ticker(symbol)["price"])
    quantity = round(trade_amount / price, 8)

    # Check Coinbase minimum trade size
    if quantity < 0.0001:
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

# === Run server ===
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
