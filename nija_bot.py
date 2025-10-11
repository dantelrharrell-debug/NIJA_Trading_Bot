#!/usr/bin/env python3
import os
import time
from coinbase.rest import RESTClient
import pandas as pd

# ===============================
# 🔐 Load Coinbase credentials
# ===============================
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ Missing API_KEY or API_SECRET environment variables")

# ===============================
# ✅ Initialize Coinbase client
# ===============================
try:
    client = RESTClient(api_key=API_KEY, api_secret=API_SECRET)
    print("✅ RESTClient created using API_KEY + API_SECRET")
except Exception as e:
    raise SystemExit(f"❌ Failed to start Coinbase client: {type(e).__name__} {e}")

# ===============================
# Configurable trading parameters
# ===============================
TRADING_SYMBOL = "BTC-USD"
MIN_RISK_PCT = 0.02  # 2%
MAX_RISK_PCT = 0.10  # 10%
VWAP_LOOKBACK = 14
RSI_PERIOD = 14
CHECK_INTERVAL = 30  # seconds

# ===============================
# Fetch balances
# ===============================
def get_balances():
    try:
        balances = client.get_account_balances()
        balance_dict = {acct['currency']: float(acct['available']) for acct in balances}
        return balance_dict
    except Exception as e:
        print("❌ Failed to fetch balances:", type(e).__name__, e)
        return {}

# ===============================
# Fetch historical candle data
# ===============================
def get_candles(symbol=TRADING_SYMBOL, granularity=60, limit=50):
    """
    Returns a pandas DataFrame of historical candles for VWAP/RSI calculations
    granularity=60 -> 1 min candles
    """
    try:
        candles = client.get_candles(product_id=symbol, granularity=granularity, limit=limit)
        df = pd.DataFrame(candles)
        df = df[['time', 'open', 'high', 'low', 'close', 'volume']]
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        return df
    except Exception as e:
        print("❌ Failed to fetch candles:", type(e).__name__, e)
        return pd.DataFrame()

# ===============================
# Calculate VWAP
# ===============================
def calculate_vwap(df):
    return (df['close'] * df['volume']).sum() / df['volume'].sum()

# ===============================
# Calculate RSI
# ===============================
def calculate_rsi(df, period=RSI_PERIOD):
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

# ===============================
# Determine trade size
# ===============================
def get_trade_amount(balance, price):
    risk = min(max(balance['USD'] * MIN_RISK_PCT, balance['USD'] * MAX_RISK_PCT), balance['USD'] * MIN_RISK_PCT)
    return round(risk / price, 6)

# ===============================
# Place market buy/sell
# ===============================
def place_order(side, size):
    try:
        order = client.create_order(
            product_id=TRADING_SYMBOL,
            side=side,
            type="market",
            size=size
        )
        print(f"✅ Placed {side.upper()} order: {size} {TRADING_SYMBOL}")
        return order
    except Exception as e:
        print(f"❌ Failed to place {side} order:", type(e).__name__, e)
        return None

# ===============================
# Main trading loop
# ===============================
def main_loop():
    print("🚀 Nija bot running...")
    while True:
        balances = get_balances()
        if not balances or 'USD' not in balances:
            print("❌ No USD balance, skipping cycle")
            time.sleep(CHECK_INTERVAL)
            continue

        df = get_candles()
        if df.empty:
            time.sleep(CHECK_INTERVAL)
            continue

        vwap = calculate_vwap(df)
        rsi = calculate_rsi(df)

        current_price = df['close'].iloc[-1]

        print(f"💹 Price: {current_price}, VWAP: {vwap}, RSI: {rsi}")

        # --- Aggressive but safe trade logic
        if current_price > vwap and rsi < 70:
            # Buy signal
            size = get_trade_amount(balances, current_price)
            place_order("buy", size)
        elif current_price < vwap and rsi > 30:
            # Sell signal
            size = get_trade_amount(balances, current_price)
            place_order("sell", size)
        else:
            print("ℹ️ No trade signal this cycle")

        time.sleep(CHECK_INTERVAL)

# ===============================
# Start bot
# ===============================
if __name__ == "__main__":
    main_loop()
