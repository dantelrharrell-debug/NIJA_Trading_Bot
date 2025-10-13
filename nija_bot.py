# nija_bot_full.py
import os
import time
import pandas as pd
import requests
from coinbase_advanced_py import Client

# -----------------------------
# 1️⃣ Load API credentials
# -----------------------------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    raise SystemExit("❌ API_KEY or API_SECRET not set.")

try:
    cb_client = Client(API_KEY, API_SECRET)
    print("✅ Coinbase client initialized.")
except Exception as e:
    raise SystemExit(f"❌ Failed to initialize Coinbase client: {e}")

# -----------------------------
# 2️⃣ Helper functions
# -----------------------------
def get_account_balance(currency):
    try:
        accounts = cb_client.get_accounts()
        for acct in accounts:
            if acct["currency"] == currency:
                return float(acct["balance"]["amount"])
        return 0.0
    except Exception as e:
        print(f"❌ Error fetching {currency} balance:", e)
        return 0.0

def place_market_order(symbol, side, size):
    try:
        order = cb_client.place_order(
            product_id=symbol,
            side=side,
            type="market",
            size=size
        )
        print(f"✅ {side.upper()} order placed for {size} {symbol}")
        return order
    except Exception as e:
        print(f"❌ Failed to place {side} order for {symbol}:", e)
        return None

def fetch_candles(symbol, granularity=300):
    """Fetch latest candle data (5-min default) from Coinbase Pro API"""
    url = f"https://api.pro.coinbase.com/products/{symbol}/candles?granularity={granularity}"
    try:
        data = requests.get(url).json()
        df = pd.DataFrame(data, columns=["time", "low", "high", "open", "close", "volume"])
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        return df.sort_values("time")
    except Exception as e:
        print(f"❌ Failed to fetch candles for {symbol}: {e}")
        return pd.DataFrame()

def calculate_vwap(df):
    """Calculate VWAP"""
    q = df["volume"]
    p = df["close"]
    vwap = (p * q).cumsum() / q.cumsum()
    return vwap.iloc[-1]

def calculate_rsi(df, period=14):
    """Calculate RSI"""
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def generate_signal(symbol):
    df = fetch_candles(symbol)
    if df.empty or len(df) < 15:
        return None
    vwap = calculate_vwap(df)
    rsi = calculate_rsi(df)
    last_close = df["close"].iloc[-1]

    # ⚡ Strategy thresholds (your pre-defined logic)
    if last_close > vwap and rsi < 70:
        return "buy"
    elif last_close < vwap and rsi > 30:
        return "sell"
    else:
        return None

# -----------------------------
# 3️⃣ Multi-ticker setup
# -----------------------------
TICKERS = ["BTC-USD", "ETH-USD", "SOL-USD", "LTC-USD", "ADA-USD", "BNB-USD", "DOGE-USD"]  # all your tickers
MIN_POSITION = 0.02  # 2% of total equity
MAX_POSITION = 0.10  # 10% of total equity

print("🚀 Starting full multi-ticker trading loop...")

# -----------------------------
# 4️⃣ Trading loop
# -----------------------------
def calculate_position_size(symbol, usd_balance, crypto_balance):
    """Dynamic position sizing between 2%-10% based on total equity"""
    try:
        last_price = fetch_candles(symbol).iloc[-1]["close"]
        total_equity = usd_balance + sum(get_account_balance(t.split("-")[0]) * fetch_candles(t).iloc[-1]["close"] for t in TICKERS)
        position = total_equity * 0.05  # default 5% per trade
        position = max(MIN_POSITION, min(MAX_POSITION, position))
        size = round(position / last_price, 8)
        return size
    except Exception as e:
        print(f"❌ Error calculating position size for {symbol}:", e)
        return 0.0

while True:
    try:
        usd_balance = get_account_balance("USD")
        print(f"💵 USD Balance: {usd_balance}")

        for ticker in TICKERS:
            print(f"🔹 Checking signals for {ticker}...")
            signal = generate_signal(ticker)
            print(f"   Signal: {signal}")

            crypto_symbol = ticker.split("-")[0]
            crypto_balance = get_account_balance(crypto_symbol)
            size = calculate_position_size(ticker, usd_balance, crypto_balance)

            if signal == "buy" and usd_balance > 10:  # ensure enough USD
                place_market_order(ticker, "buy", size)
            elif signal == "sell" and crypto_balance * fetch_candles(ticker).iloc[-1]["close"] > 10:  # enough crypto
                place_market_order(ticker, "sell", size)

        time.sleep(30)  # loop every 30 seconds
    except KeyboardInterrupt:
        print("🛑 Trading loop stopped by user.")
        break
    except Exception as e:
        print("❌ Trading loop error:", e)
        time.sleep(10)
