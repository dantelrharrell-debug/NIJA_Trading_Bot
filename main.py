from fastapi import FastAPI, Request
import uvicorn
import coinbase_advanced_py as cb
import os
import time

# ======================
# CONFIG
# ======================
api_key = "f0e7ae67-cf8a-4aee-b3cd-17227a1b8267"
api_secret = "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49"
SANDBOX = False  # True=test, False=live
DEFAULT_TRADE_AMOUNT = 10
MAX_TRADE_AMOUNT = 100
MIN_USD_BALANCE = 5
TRADE_HISTORY_LIMIT = 50
STOP_LOSS_PERCENT = 0.05  # 5% loss
TAKE_PROFIT_PERCENT = 0.10  # 10% gain

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
# TRADE & POSITION TRACKING
# ======================
trade_history = []
open_positions = {}  # {coin: [positions]}
session_pnl = 0

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

def get_crypto_balance(symbol):
    crypto = symbol.split("-")[0]
    try:
        accounts = client.get_accounts()
        for acc in accounts:
            if acc['currency'] == crypto:
                return float(acc['balance'])
    except Exception as e:
        print(f"❌ Error fetching balance for {symbol}:", e)
    return 0.0

def get_price(symbol):
    try:
        ticker = client.get_product_ticker(symbol)
        return float(ticker['price'])
    except Exception as e:
        print(f"❌ Error fetching price for {symbol}:", e)
        return 0.0

def calculate_pnl(symbol, action, amount_usd, price):
    global session_pnl
    crypto = symbol.split("-")[0]

    if action.lower() == "buy":
        if crypto not in open_positions:
            open_positions[crypto] = []
        open_positions[crypto].append({"amount_usd": amount_usd, "price": price})
        return 0

    elif action.lower() == "sell":
        if crypto not in open_positions or len(open_positions[crypto]) == 0:
            return 0
        position = open_positions[crypto].pop(0)
        bought_usd = position["amount_usd"]
        bought_price = position["price"]
        pnl = (price - bought_price) / bought_price * bought_usd
        session_pnl += pnl
        return pnl
    return 0

def check_stop_take(symbol):
    crypto = symbol.split("-")[0]
    if crypto not in open_positions:
        return
    price = get_price(symbol)
    for pos in open_positions[crypto][:]:
        bought_price = pos["price"]
        pnl_percent = (price - bought_price) / bought_price
        if pnl_percent <= -STOP_LOSS_PERCENT:
            print(f"⚠ Stop-loss hit for {crypto} at price {price}")
            place_order(symbol, "sell", pos["amount_usd"])
            open_positions[crypto].remove(pos)
        elif pnl_percent >= TAKE_PROFIT_PERCENT:
            print(f"💰 Take-profit hit for {crypto} at price {price}")
            place_order(symbol, "sell", pos["amount_usd"])
            open_positions[crypto].remove(pos)

def place_order(symbol, side, amount_usd):
    if amount_usd > MAX_TRADE_AMOUNT:
        amount_usd = MAX_TRADE_AMOUNT

    usd_balance = get_usd_balance()
    if side.lower() == "buy" and usd_balance < MIN_USD_BALANCE:
        print(f"⚠ USD balance too low (${usd_balance}). Trade skipped")
        return None

    crypto_balance = get_crypto_balance(symbol)
    if side.lower() == "sell" and crypto_balance <= 0:
        print(f"⚠ No crypto to sell ({symbol}). Trade skipped")
        return None

    price = get_price(symbol)
    print(f"📌 Placing {side.upper()} for ${amount_usd} of {symbol} at price ${price}")

    try:
        order = client.place_order(
            product_id=symbol,
            side=side,
            order_type="market",
            funds=str(amount_usd)
        )
        pnl = calculate_pnl(symbol, side, amount_usd, price)
        trade_history.append({
            "symbol": symbol,
            "action": side.lower(),
            "amount": amount_usd,
            "price": price,
            "pnl": pnl
        })
        if len(trade_history) > TRADE_HISTORY_LIMIT:
            trade_history.pop(0)
        print(f"✅ Order executed. PnL: {pnl:.2f}, Session PnL: {session_pnl:.2f}")
        return order
    except Exception as e:
        print(f"❌ Order failed: {e}")
        return None

def adjust_trade_amount(default_amount):
    if len(trade_history) < 3:
        return default_amount
    recent = trade_history[-3:]
    wins = sum(1 for t in recent if t["pnl"] > 0)
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

    # Check stop-loss / take-profit first
    check_stop_take(symbol)

    if action.lower() not in ["buy", "sell"]:
        return {"status": "error", "message": "Invalid action"}

    order = place_order(symbol, action.lower(), amount)
    if order:
        return {"status": "success", "message": f"{action.upper()} order placed for {symbol}"}
    else:
        return {"status": "error", "message": "Order failed"}

# ======================
# RUN BOT
# ======================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
