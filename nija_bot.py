# =============================
# nija_bot.py
# Render-ready Coinbase Advanced Bot
# =============================

import os
import time
import pandas as pd
from dotenv import load_dotenv
import coinbase_advanced_py as cb

# =============================
# Load environment variables
# =============================
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SANDBOX = os.getenv("SANDBOX", "False") == "True"
SYMBOLS = os.getenv("TRADE_SYMBOLS", "BTC-USD").split(",")
TRADE_AMOUNT = float(os.getenv("TRADE_AMOUNT", 10))
MIN_RISK = float(os.getenv("MIN_RISK", 0.02))
MAX_RISK = float(os.getenv("MAX_RISK", 0.10))
PRICE_HISTORY_LENGTH = int(os.getenv("PRICE_HISTORY_LENGTH", 50))
SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", 10))
TP_PERCENT = float(os.getenv("TP_PERCENT", 1.0))
SL_PERCENT = float(os.getenv("SL_PERCENT", 1.0))

if not API_KEY or not API_SECRET:
    raise ValueError("❌ Missing API_KEY or API_SECRET")

client = cb.Client(API_KEY, API_SECRET, sandbox=SANDBOX)
print("🚀 Coinbase Advanced client initialized")

# =============================
# Open positions tracker
# =============================
open_positions = {symbol: [] for symbol in SYMBOLS}

# =============================
# Helper functions
# =============================
def get_equity():
    balances = client.get_account_balances()
    total = sum(float(b['available']) + float(b['hold']) for b in balances.values())
    return total

def calculate_position_size(equity):
    pct = max(MIN_RISK, min(MAX_RISK, equity/100))
    return pct

def fetch_candles(symbol, limit=PRICE_HISTORY_LENGTH):
    try:
        candles = client.get_historical_prices(symbol, granularity="1m", limit=limit)
        df = pd.DataFrame(candles)
        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"❌ Error fetching candles for {symbol}: {e}")
        return pd.DataFrame()

def compute_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_vwap(df):
    return (df['close'] * df['close']).cumsum() / df['close'].cumsum()

def get_signal(df):
    df['RSI'] = compute_rsi(df['close'])
    df['VWAP'] = compute_vwap(df)
    last = df.iloc[-1]

    if last['RSI'] < 30 and last['close'] < last['VWAP']:
        return "buy", last['close']*(1-SL_PERCENT/100), last['close']*(1+TP_PERCENT/100)
    elif last['RSI'] > 70 and last['close'] > last['VWAP']:
        return "sell", last['close']*(1+SL_PERCENT/100), last['close']*(1-TP_PERCENT/100)
    return None, None, None

def place_trade(symbol, side, size, stop_loss=None, take_profit=None):
    try:
        print(f"💰 Placing {side} trade for {symbol}: size={size}, SL={stop_loss}, TP={take_profit}")
        order = client.place_order(symbol=symbol, side=side, size=size)
        return order
    except Exception as e:
        print(f"❌ Error placing trade for {symbol}: {e}")
        return None

def check_exit(position, current_price):
    if position['side'] == 'buy':
        if current_price >= position.get('take_profit', 0):
            print(f"✅ Take-profit hit for {position['symbol']}")
            return True
        if current_price <= position.get('stop_loss', 0):
            print(f"⚠ Stop-loss hit for {position['symbol']}")
            return True
    elif position['side'] == 'sell':
        if current_price <= position.get('take_profit', 0):
            print(f"✅ Take-profit hit for {position['symbol']}")
            return True
        if current_price >= position.get('stop_loss', 0):
            print(f"⚠ Stop-loss hit for {position['symbol']}")
            return True
    return False

# =============================
# Main trading loop
# =============================
def main():
    print("🔥 Starting multi-symbol aggressive bot...")
    while True:
        try:
            equity = get_equity()
            size = calculate_position_size(equity)

            for symbol in SYMBOLS:
                candles = fetch_candles(symbol)
                if candles.empty:
                    continue
                current_price = candles['close'].iloc[-1]

                # Check open positions
                for pos in open_positions[symbol][:]:
                    if check_exit(pos, current_price):
                        open_positions[symbol].remove(pos)

                # New trade signal
                signal, sl, tp = get_signal(candles)
                if signal:
                    position = place_trade(symbol, signal, size, stop_loss=sl, take_profit=tp)
                    if position:
                        open_positions[symbol].append(position)
                else:
                    print(f"⏸ No trade signal for {symbol}")

            time.sleep(SLEEP_INTERVAL)

        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
