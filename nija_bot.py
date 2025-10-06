#!/usr/bin/env python3
import os
import time
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import coinbase_advanced_py as cb
import requests

# =============================
# Load API keys
# =============================
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise ValueError("❌ API_KEY or API_SECRET missing")

# =============================
# Initialize Coinbase client
# =============================
client = cb.Client(API_KEY, API_SECRET)
print("✅ Coinbase client initialized")

# =============================
# Trading parameters
# =============================
MIN_POSITION = 0.02  # 2% of equity
MAX_POSITION = 0.10  # 10% of equity
SYMBOL = "BTC-USD"   # trading symbol
TRADE_INTERVAL = 10  # seconds between checks
CANDLE_INTERVAL = "1m"  # timeframe for indicators
HISTORY_LIMIT = 100  # number of historical candles to fetch

# =============================
# Indicator calculations
# =============================
def fetch_candles(symbol, interval="1m", limit=100):
    """Fetch historical candles from Coinbase"""
    url = f"https://api.exchange.coinbase.com/products/{symbol}/candles"
    params = {"granularity": 60, "limit": limit}  # 1m candles
    try:
        resp = requests.get(url, params=params)
        data = resp.json()
        df = pd.DataFrame(data, columns=["time", "low", "high", "open", "close", "volume"])
        df.sort_values("time", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
    except Exception as e:
        print("❌ Failed to fetch candles:", e)
        return pd.DataFrame()

def vwap(df):
    """Calculate VWAP"""
    return (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()

def rsi(df, period=14):
    """Calculate RSI"""
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def atr(df, period=14):
    """Calculate ATR"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()

# =============================
# Account & trade functions
# =============================
def get_balances():
    balances = client.get_account_balances()
    return balances

def get_equity():
    balances = get_balances()
    total_equity = 0.0
    for sym, info in balances.items():
        try:
            total_equity += float(info['available'])
        except:
            continue
    return total_equity

def calculate_position_size(equity):
    """Return trade size between MIN_POSITION and MAX_POSITION of equity"""
    size = equity * 0.05  # example: 5% of current equity
    min_size = equity * MIN_POSITION
    max_size = equity * MAX_POSITION
    return max(min_size, min(size, max_size))

def get_signal(df):
    """Generate signal based on VWAP, RSI, ATR"""
    df['vwap'] = vwap(df)
    df['rsi'] = rsi(df)
    df['atr'] = atr(df)
    
    last_close = df['close'].iloc[-1]
    last_vwap = df['vwap'].iloc[-1]
    last_rsi = df['rsi'].iloc[-1]

    # Basic signal logic:
    if last_close > last_vwap and last_rsi < 70:
        return "buy"
    elif last_close < last_vwap and last_rsi > 30:
        return "sell"
    return None

def place_trade(signal, size):
    if signal not in ["buy", "sell"]:
        return
    try:
        order = client.place_order(
            symbol=SYMBOL,
            side=signal,
            type="market",
            size=size
        )
        print(f"🚀 Placed {signal} order for {size} {SYMBOL}")
        return order
    except Exception as e:
        print("❌ Order failed:", e)

# =============================
# Main loop
# =============================
def main():
    print("🔥 Starting real indicator-based trading loop...")
    while True:
        try:
            equity = get_equity()
            size = calculate_position_size(equity)
            
            candles = fetch_candles(SYMBOL, interval=CANDLE_INTERVAL, limit=HISTORY_LIMIT)
            if candles.empty:
                print("⏸ No candle data, skipping...")
                time.sleep(TRADE_INTERVAL)
                continue
            
            signal = get_signal(candles)
            if signal:
                place_trade(signal, size)
            else:
                print("⏸ No trade signal")
            
            time.sleep(TRADE_INTERVAL)
        except Exception as e:
            print("❌ Error in main loop:", e)
            time.sleep(5)

if __name__ == "__main__":
    main()
