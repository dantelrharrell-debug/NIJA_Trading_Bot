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
if not API_KEY or not API_SECRET:
    raise ValueError("❌ API_KEY or API_SECRET missing")

client = cb.Client(API_KEY, API_SECRET)
print("🚀 Coinbase client initialized")

# =============================
# Bot settings
# =============================
SYMBOLS = ["BTC-USD", "ETH-USD", "LTC-USD"]
TRADE_INTERVAL = 60  # in seconds
CANDLE_INTERVAL = "1m"  # 1-minute candles
HISTORY_LIMIT = 50
MIN_SIZE_PCT = 0.02
MAX_SIZE_PCT = 0.10
RSI_PERIOD = 14
VWAP_PERIOD = 14
open_positions = {symbol: [] for symbol in SYMBOLS}

# =============================
# Helper functions
# =============================
def get_equity():
    balances = client.get_account_balances()
    total = sum(float(b['available']) + float(b['hold']) for b in balances.values())
    return total

def calculate_position_size(equity):
    pct = max(MIN_SIZE_PCT, min(MAX_SIZE_PCT, equity/100))
    return pct

def fetch_candles(symbol, interval="1m", limit=50):
    try:
        candles = client.get_historical_prices(symbol, granularity=interval, limit=limit)
        df = pd.DataFrame(candles)
        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"❌ Error fetching candles for {symbol}:", e)
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
    df['RSI'] = compute_rsi(df['close'], RSI_PERIOD)
    df['VWAP'] = compute_vwap(df)
    last = df.iloc[-1]
    
    if last['RSI'] < 30 and last['close'] < last['VWAP']:
        return "buy", last['close']*0.99, last['close']*1.01  # stop-loss, take-profit
    elif last['RSI'] > 70 and last['close'] > last['VWAP']:
        return "sell", last['close']*1.01, last['close']*0.99
    return None, None, None

def place_trade(side, size, stop_loss=None, take_profit=None):
    try:
        print(f"💰 Placing {side} trade: size={size}, SL={stop_loss}, TP={take_profit}")
        order = client.place_order(symbol=symbol, side=side, size=size)
        return order
    except Exception as e:
        print("❌ Error placing trade:", e)
        return None

def check_exit(position, current_price):
    if position['side'] == 'buy' and current_price >= position.get('take_profit', 0):
        print(f"✅ Take-profit hit for {position['symbol']}")
        return True
    if position['side'] == 'buy' and current_price <= position.get('stop_loss', 0):
        print(f"⚠ Stop-loss hit for {position['symbol']}")
        return True
    if position['side'] == 'sell' and current_price <= position.get('take_profit', 0):
        print(f"✅ Take-profit hit for {position['symbol']}")
        return True
    if position['side'] == 'sell' and current_price >= position.get('stop_loss', 0):
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
                candles = fetch_candles(symbol, interval=CANDLE_INTERVAL, limit=HISTORY_LIMIT)
                if candles.empty:
                    continue
                current_price = candles['close'].iloc[-1]

                # Check open positions
                for pos in open_positions[symbol][:]:
                    if check_exit(pos, current_price):
                        open_positions[symbol].remove(pos)

                # New signal
                signal, sl, tp = get_signal(candles)
                if signal:
                    position = place_trade(signal, size, stop_loss=sl, take_profit=tp)
                    if position:
                        open_positions[symbol].append(position)
                else:
                    print(f"⏸ No trade signal for {symbol}")

            time.sleep(TRADE_INTERVAL)

        except Exception as e:
            print("❌ Error in main loop:", e)
            time.sleep(5)

if __name__ == "__main__":
    main()
