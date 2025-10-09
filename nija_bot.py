import os
import time
import pandas as pd
from dotenv import load_dotenv

# =============================
# Load environment variables
# =============================
load_dotenv()

# Coinbase API keys
SPOT_KEY = os.getenv("COINBASE_SPOT_KEY")
SPOT_SECRET = os.getenv("COINBASE_SPOT_SECRET")
SPOT_PASSPHRASE = os.getenv("COINBASE_SPOT_PASSPHRASE")

FUTURES_KEY = os.getenv("COINBASE_FUTURES_KEY")
FUTURES_SECRET = os.getenv("COINBASE_FUTURES_SECRET")
FUTURES_PASSPHRASE = os.getenv("COINBASE_FUTURES_PASSPHRASE")

# Bot settings
TP_PERCENT = float(os.getenv("TP_PERCENT", 1.0))
SL_PERCENT = float(os.getenv("SL_PERCENT", 1.0))
TRAILING_STOP = float(os.getenv("TRAILING_STOP", 0.5))
TRAILING_TP = float(os.getenv("TRAILING_TP", 0.5))
SMART_LOGIC = os.getenv("SMART_LOGIC", "False").lower() == "true"
DRY_RUN = os.getenv("DRY_RUN", "False").lower() == "true"
SANDBOX = os.getenv("SANDBOX", "False").lower() == "true"

TRADE_SYMBOLS = os.getenv("TRADE_SYMBOLS", "BTC-USD").split(",")
DEFAULT_TRADE_AMOUNT = float(os.getenv("DEFAULT_TRADE_AMOUNT", 10))
MAX_TRADE_AMOUNT = float(os.getenv("MAX_TRADE_AMOUNT", 100))
MIN_TRADE_AMOUNT = float(os.getenv("MIN_TRADE_AMOUNT", 10))
MIN_RISK = float(os.getenv("MIN_RISK", 0.02))
MAX_RISK = float(os.getenv("MAX_RISK", 0.10))

TRADE_HISTORY_LIMIT = int(os.getenv("TRADE_HISTORY_LIMIT", 200))
PRICE_HISTORY_LENGTH = int(os.getenv("PRICE_HISTORY_LENGTH", 50))
SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", 10))

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "YourStrongSecretHere")
TRADINGVIEW_WEBHOOK = os.getenv("TRADINGVIEW_WEBHOOK")
PORT = int(os.getenv("PORT", 10000))

LEARNING_FILE = os.getenv("LEARNING_FILE", "trade_learning.json")
BASE_STOP_LOSS = float(os.getenv("BASE_STOP_LOSS", 0.05))
BASE_TAKE_PROFIT = float(os.getenv("BASE_TAKE_PROFIT", 0.10))
FUTURES_AVAILABLE = os.getenv("FUTURES_AVAILABLE", "True").lower() == "true"

# =============================
# Import Coinbase SDK
# =============================
try:
    import coinbase_advanced_py as cb
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "coinbase_advanced_py not installed. Run:\n"
        "pip install coinbase-advanced-py==1.8.2"
    )

# =============================
# Initialize client
# =============================
client = cb.Client(SPOT_KEY, SPOT_SECRET)
print("🚀 Coinbase client initialized")

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

def fetch_candles(symbol, interval="1m", limit=PRICE_HISTORY_LENGTH):
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
    df['RSI'] = compute_rsi(df['close'], 14)
    df['VWAP'] = compute_vwap(df)
    last = df.iloc[-1]
    
    if last['RSI'] < 30 and last['close'] < last['VWAP']:
        return "buy", last['close'] * (1 - SL_PERCENT/100), last['close'] * (1 + TP_PERCENT/100)
    elif last['RSI'] > 70 and last['close'] > last['VWAP']:
        return "sell", last['close'] * (1 + SL_PERCENT/100), last['close'] * (1 - TP_PERCENT/100)
    return None, None, None

def place_trade(symbol, side, size, stop_loss=None, take_profit=None):
    try:
        print(f"💰 Placing {side} trade for {symbol}: size={size}, SL={stop_loss}, TP={take_profit}")
        if DRY_RUN:
            return {"symbol": symbol, "side": side, "size": size, "stop_loss": stop_loss, "take_profit": take_profit}
        order = client.place_order(symbol=symbol, side=side, size=size)
        return order
    except Exception as e:
        print("❌ Error placing trade:", e)
        return None

# =============================
# Main trading loop
# =============================
open_positions = {symbol: [] for symbol in TRADE_SYMBOLS}

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

def main():
    print("🔥 Starting multi-symbol bot...")
    while True:
        try:
            equity = get_equity()
            size = calculate_position_size(equity)
            
            for symbol in TRADE_SYMBOLS:
                candles = fetch_candles(symbol)
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
                    position = place_trade(symbol, signal, size, stop_loss=sl, take_profit=tp)
                    if position:
                        open_positions[symbol].append(position)
                else:
                    print(f"⏸ No trade signal for {symbol}")

            time.sleep(SLEEP_INTERVAL)

        except Exception as e:
            print("❌ Error in main loop:", e)
            time.sleep(5)

if __name__ == "__main__":
    main()
