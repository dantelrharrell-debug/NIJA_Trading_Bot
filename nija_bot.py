from fastapi import FastAPI, Request
import uvicorn
import coinbase_advanced_py as cb
import os
import logging
from fastapi import FastAPI

logger = logging.getLogger("nija")
import time

# ======================
# CONFIG
# ======================
api_key = "f0e7ae67-cf8a-4aee-b3cd-17227a1b8267"
api_secret = "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49"
SANDBOX = False  # True=test, False=live
DEFAULT_TRADE_AMOUNT = 10  # USD per trade
MAX_TRADE_AMOUNT = 100  # Max trade cap
MIN_USD_BALANCE = 5  # Don't trade below this balance
TRADE_HISTORY_LIMIT = 20  # Keep last 20 trades for learning

# ======================
# CONNECT TO COINBASE
# ======================
try:
    client = cb.CoinbaseAdvanced(api_key=api_key, api_secret=api_secret, sandbox=SANDBOX)
    print("✅ Connected to Coinbase Advanced")
except Exception as e:
    print("❌ Failed to connect:", e)
    exit(1)

# ======================
# FASTAPI SETUP
# ======================
app = FastAPI()

# ======================
# TRADE HISTORY
# ======================
trade_history = []

# ======================
# HELPERS
# ======================
def get_usd_balance():
    try:
        accounts = client.get_accounts()
        for acc in accounts:
            if acc['currency'] == "USD":
                return float(acc['balance'])
    except Exception as e:
        print("❌ Error fetching USD balance:", e)
    return 0.0

def get_price(symbol):
    try:
        ticker = client.get_product_ticker(symbol)
        return float(ticker['price'])
    except Exception as e:
        print(f"❌ Error fetching price for {symbol}:", e)
        return 0.0

def place_order(symbol, side, amount_usd):
    if amount_usd > MAX_TRADE_AMOUNT:
        print(f"⚠ Trade amount ${amount_usd} exceeds max. Capped to {MAX_TRADE_AMOUNT}")
        amount_usd = MAX_TRADE_AMOUNT

    usd_balance = get_usd_balance()
    if usd_balance < MIN_USD_BALANCE:
        print(f"⚠ USD balance too low (${usd_balance}). Trade skipped")
        return None

    print(f"📌 Placing {side.upper()} for ${amount_usd} of {symbol}")
    try:
        order = client.place_order(
            product_id=symbol,
            side=side,
            order_type="market",
            funds=str(amount_usd)
        )
        print(f"✅ Order successful: {order}")
        return order
    except Exception as e:
        print(f"❌ Order failed: {e}")
        return None

def adjust_trade_amount(default_amount):
    if len(trade_history) < 3:
        return default_amount
    recent = trade_history[-3:]
    wins = sum(1 for t in recent if t.get("result", 0) > 0)
    if wins >= 2:
        return min(default_amount * 1.1, MAX_TRADE_AMOUNT)
    else:
        return max(default_amount * 0.9, 1)

# ======================
# WEBHOOK ENDPOINT
# ======================
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("⚡ Webhook received:", data)

    action = data.get("action")
    symbol = data.get("symbol", "BTC-USD")
    amount = float(data.get("amount", DEFAULT_TRADE_AMOUNT))

    # Adaptive trade sizing
    amount = adjust_trade_amount(amount)

    if action.lower() not in ["buy", "sell"]:
        return {"status": "error", "message": "Invalid action"}

    order = place_order(symbol, action.lower(), amount)
    if order:
        trade_history.append({
            "symbol": symbol,
            "action": action.lower(),
            "amount": amount,
            "result": 0,  # placeholder for PnL
            "price": get_price(symbol)
        })
        if len(trade_history) > TRADE_HISTORY_LIMIT:
            trade_history.pop(0)  # keep history limited
        return {"status": "success", "message": f"{action.upper()} order placed for {symbol}"}
    else:
        return {"status": "error", "message": "Order failed"}

# ======================
# RUN BOT
# ======================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
