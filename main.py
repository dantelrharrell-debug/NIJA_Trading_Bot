# main.py
import subprocess
import sys
import time

# 1️⃣ Ensure coinbase-advanced-py is installed
try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "coinbase-advanced-py==1.8.2"])
    import coinbase_advanced_py as cb

print("✅ coinbase_advanced_py module ready!")

# 2️⃣ API keys
API_KEY = "f0e7ae67-cf8a-4aee-b3cd-17227a1b8267"
API_SECRET = "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49"

# 3️⃣ Initialize client
client = cb.CoinbaseAdvanced(API_KEY, API_SECRET)

# 4️⃣ Minimum trade amounts
MIN_TRADE = {"BTC-USD": 0.0001, "ETH-USD": 0.001}

# 5️⃣ Risk bounds
MIN_RISK = 0.02
MAX_RISK = 0.10

# 6️⃣ Function to get current balance
def get_balance():
    accounts = client.get_accounts()
    balance_usd = float([acc['balance'] for acc in accounts if acc['currency'] == 'USD'][0])
    return balance_usd

# 7️⃣ Placeholder AI risk function
def get_ai_signal(symbol):
    """Return AI risk factor between 0.02 and 0.10"""
    import random
    ai_risk = random.uniform(MIN_RISK, MAX_RISK)
    print(f"🤖 AI risk for {symbol}: {ai_risk*100:.2f}%")
    return ai_risk

# 8️⃣ Calculate trade size based on AI risk
def calculate_trade_size(symbol, ai_risk):
    balance_usd = get_balance()
    risk = max(MIN_RISK, min(MAX_RISK, ai_risk))
    trade_usd = balance_usd * risk
    try:
        price = float(client.get_product_ticker(symbol)['price'])
        quantity = max(trade_usd / price, MIN_TRADE.get(symbol, 0))
        return round(quantity, 8)  # rounding for Coinbase precision
    except Exception as e:
        print(f"❌ Error calculating trade size for {symbol}: {e}")
        return 0

# 9️⃣ Place market order
def place_order(symbol, side):
    ai_risk = get_ai_signal(symbol)
    quantity = calculate_trade_size(symbol, ai_risk)
    if quantity <= 0:
        print(f"⚠️ Trade too small for {symbol}. Skipping.")
        return
    try:
        order = client.place_order(
            symbol=symbol,
            side=side,
            order_type="market",
            quantity=quantity
        )
        print(f"✅ {side.upper()} order executed: {quantity} {symbol}")
        return order
    except Exception as e:
        print(f"❌ Failed to place order for {symbol}: {e}")

# 🔁 Continuous trading loop
symbols = ["BTC-USD", "ETH-USD"]
sides = ["buy", "sell"]  # Example alternating strategy
INTERVAL = 10  # seconds between AI adjustments

print("🤖 Dynamic AI Risk Management Bot is live!")

try:
    while True:
        for i, symbol in enumerate(symbols):
            place_order(symbol, sides[i])
        time.sleep(INTERVAL)  # adjust risk every INTERVAL seconds
except KeyboardInterrupt:
    print("🛑 Bot stopped by user")
