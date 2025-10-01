import subprocess
import sys
import time
import numpy as np
import pandas as pd

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

# 6️⃣ Get current balance
def get_balance():
    accounts = client.get_accounts()
    balance_usd = float([acc['balance'] for acc in accounts if acc['currency'] == 'USD'][0])
    return balance_usd

# 7️⃣ Fetch historical prices
def get_historical_prices(symbol, limit=50):
    try:
        candles = client.get_historic_rates(symbol, granularity=60)  # 1-minute candles
        df = pd.DataFrame(candles, columns=['time','low','high','open','close','volume'])
        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"❌ Error fetching historical prices: {e}")
        return pd.DataFrame()

# 8️⃣ AI risk calculation based on market conditions
def get_ai_signal(symbol):
    df = get_historical_prices(symbol)
    if df.empty:
        return MIN_RISK
    
    # Volatility: standard deviation of recent closes
    volatility = df['close'].pct_change().std()
    
    # Trend: 10-period vs 20-period moving average
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    trend_strength = abs(df['ma10'].iloc[-1] - df['ma20'].iloc[-1]) / df['ma20'].iloc[-1]
    
    # Momentum: last close % change
    momentum = df['close'].pct_change().iloc[-1]
    
    # AI logic: more volatility → lower risk; strong trend → higher risk; momentum aligns direction
    risk = (trend_strength * 0.6) - (volatility * 0.5) + (abs(momentum) * 0.3)
    risk = max(MIN_RISK, min(MAX_RISK, risk))
    
    print(f"🤖 {symbol} AI risk: {risk*100:.2f}% | Vol: {volatility:.4f}, Trend: {trend_strength:.4f}, Mom: {momentum:.4f}")
    return risk

# 9️⃣ Calculate trade size
def calculate_trade_size(symbol, ai_risk):
    balance_usd = get_balance()
    trade_usd = balance_usd * ai_risk
    try:
        price = float(client.get_product_ticker(symbol)['price'])
        quantity = max(trade_usd / price, MIN_TRADE.get(symbol, 0))
        return round(quantity, 8)
    except Exception as e:
        print(f"❌ Error calculating trade size for {symbol}: {e}")
        return 0

# 🔟 Place order
def place_order(symbol, side):
    ai_risk = get_ai_signal(symbol)
    quantity = calculate_trade_size(symbol, ai_risk)
    if quantity <= 0:
        print(f"⚠️ Trade too small for {symbol}. Skipping.")
        return
    try:
        order = client.place_order(symbol=symbol, side=side, order_type="market", quantity=quantity)
        print(f"✅ {side.upper()} order executed: {quantity} {symbol}")
        return order
    except Exception as e:
        print(f"❌ Failed to place order for {symbol}: {e}")

# 11️⃣ Continuous loop
symbols = ["BTC-USD", "ETH-USD"]
sides = ["buy", "sell"]  # alternating example
INTERVAL = 60  # check every minute

print("🚀 AI Risk Management Bot live!")

try:
    while True:
        for i, symbol in enumerate(symbols):
            place_order(symbol, sides[i])
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print("🛑 Bot stopped by user")
