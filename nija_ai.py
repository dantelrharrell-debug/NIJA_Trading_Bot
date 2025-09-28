import ccxt, json, os, traceback
from decimal import Decimal

# Load API keys
spot = ccxt.coinbasepro({
    'apiKey': os.getenv("COINBASE_SPOT_KEY"),
    'secret': os.getenv("COINBASE_SPOT_SECRET")
})
futures = ccxt.coinbasepro({
    'apiKey': os.getenv("COINBASE_FUTURES_KEY"),
    'secret': os.getenv("COINBASE_FUTURES_SECRET")
})

TRADE_HISTORY_FILE = "trade_history.json"
try:
    with open(TRADE_HISTORY_FILE,"r") as f: trade_history = json.load(f)
except:
    trade_history = {}

def save_history():
    with open(TRADE_HISTORY_FILE,"w") as f:
        json.dump(trade_history,f,indent=2)

def ai_adjust_amount(symbol, base_amount):
    history = trade_history.get(symbol, [])
    wins = sum(1 for t in history if t.get("profit",0)>0)
    losses = sum(1 for t in history if t.get("profit",0)<0)
    multiplier = 1 + (wins - losses)*0.1
    return float(Decimal(base_amount) * Decimal(max(multiplier,0.1)))

def execute_trade(symbol, side, amount, market_type="spot"):
    client = futures if market_type=="futures" else spot
    amount = ai_adjust_amount(symbol, amount)
    try:
        order = client.create_market_order(symbol, side, amount)
        print(f"✅ Trade executed {symbol} {side} {amount}: {order}")
        trade_history.setdefault(symbol,[]).append({"side":side,"amount":float(amount),"profit":0})
        save_history()
    except Exception as e:
        print("❌ Trade failed:", repr(e))
        traceback.print_exc()
