# main.py

import subprocess
import sys
import time

# 1️⃣ Ensure coinbase-advanced-py is installed
try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    print("Module not found, installing coinbase-advanced-py...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "coinbase-advanced-py==1.8.2"])
    import coinbase_advanced_py as cb

print("✅ coinbase_advanced_py module is ready!")

# 2️⃣ API keys
API_KEY = "f0e7ae67-cf8a-4aee-b3cd-17227a1b8267"
API_SECRET = "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49"

# 3️⃣ Initialize client
client = cb.CoinbaseAdvanced(API_KEY, API_SECRET)

# 4️⃣ Test connection
try:
    accounts = client.get_accounts()
    balance_usd = float([acc['balance'] for acc in accounts if acc['currency'] == 'USD'][0])
    print(f"✅ Connection successful! USD Balance: ${balance_usd:.2f}")
except Exception as e:
    print("❌ Error connecting to Coinbase Advanced:", e)
    sys.exit(1)

# 5️⃣ Minimum trade amounts for Coinbase
MIN_TRADE = {"BTC-USD": 0.0001, "ETH-USD": 0.001}

# 6️⃣ Risk parameters (2%-10% of account)
MIN_RISK = 0.02
MAX_RISK = 0.10

# 7️⃣ Dynamic AI signal function (example placeholder)
def get_ai_signal(symbol):
    """
    Replace this with your AI model output.
    Returns risk factor between 0.0 and 1.0.
    """
    import random
    # Example: AI outputs 0.02-0.10 range randomly (simulate AI decision)
    base_risk = random.uniform(0.02, 0.10)
    print(f"🤖 AI suggested risk for {symbol}: {base_risk*100:.2f}%")
    return base_risk

# 8️⃣ Function to calculate trade size dynamically
def calculate_trade_size(symbol, ai_risk):
    risk = max(MIN_RISK, min(MAX_RISK, ai_risk))  # enforce 2%-10%
    trade_usd = balance_usd * risk
    try:
        price = float(client.get_product_ticker(symbol)['price'])
        quantity = trade_usd / price
        min_qty = MIN_TRADE.get(symbol, 0)
        quantity = max(quantity, min_qty)
        return quantity
    except Exception as e:
        print(f"❌ Failed to calculate trade size for {symbol}:", e)
        return 0

# 9️⃣ Place order function
def place_order(symbol, side):
    ai_risk = get_ai_signal(symbol)  # AI decides risk dynamically
    quantity = calculate_trade_size(symbol, ai_risk)
    if quantity <= 0:
        print(f"⚠️ Trade quantity too small or failed for {symbol}. Skipping trade.")
        return None
    try:
        print(f"\n💰 Placing {side.upper()} order for {quantity:.6f} {symbol} (risk {ai_risk*100:.2f}%)...")
        order = client.place_order(
            symbol=symbol,
            side=side,
            order_type="market",
            quantity=quantity
        )
        print("✅ Order executed:", order)
        return order
    except Exception as e:
        print("❌ Failed to execute order:", e)
        return None

# 10️⃣ Example: Automated trading loop
symbols = ["BTC-USD", "ETH-USD"]
sides = ["buy", "sell"]  # example strategy
for i, symbol in enumerate(symbols):
    place_order(symbol, sides[i])
    time.sleep(1)

print("\n🤖 Dynamic AI Risk Management Bot is live!")
