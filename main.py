import os
import time
import csv
from datetime import datetime
import coinbase_advanced_py as cb

# ======================
# CONFIG FROM ENV
# ======================
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
SANDBOX = os.getenv("SANDBOX", "True") == "True"  # True for testing
TRADING_SYMBOL = os.getenv("TRADING_SYMBOL", "BTC-USD")
TRADE_AMOUNT = float(os.getenv("TRADE_AMOUNT", 10))  # USD per trade
SLEEP_INTERVAL = int(os.getenv("SLEEP_INTERVAL", 10))  # Seconds between checks

# AI-inspired strategy settings
PRICE_HISTORY = []
LOOKBACK = 5
MOMENTUM_THRESHOLD = 0.002  # 0.2% movement triggers trade

# CSV log file
LOG_FILE = "trades.csv"

# ======================
# CONNECT TO COINBASE
# ======================
client = cb.CoinbaseAdvanced(api_key=API_KEY, api_secret=API_SECRET, sandbox=SANDBOX)
print(f"[{datetime.now()}] Connected to Coinbase Advanced (Sandbox={SANDBOX})")

# ======================
# FUNCTIONS
# ======================
def check_balance(currency="USD"):
    balances = client.get_accounts()
    for b in balances:
        if b['currency'] == currency:
            return float(b['balance'])
    return 0.0

def get_price(symbol):
    ticker = client.get_product_ticker(symbol)
    return float(ticker['price'])

def place_order(side, symbol, amount):
    print(f"[{datetime.now()}] Placing {side.upper()} order for ${amount} of {symbol}")
    try:
        order = client.place_order(product_id=symbol, side=side, order_type="market", funds=str(amount))
        print(f"[{datetime.now()}] Order details: {order}")
        log_trade(side, symbol, amount, get_price(symbol))
    except Exception as e:
        print(f"[{datetime.now()}] Order error: {e}")

def log_trade(side, symbol, usd_amount, price):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "side", "symbol", "usd_amount", "price"])
        writer.writerow([datetime.now(), side, symbol, usd_amount, price])

def nija_strategy(current_price):
    PRICE_HISTORY.append(current_price)
    if len(PRICE_HISTORY) < LOOKBACK:
        return

    momentum = (current_price - PRICE_HISTORY[-LOOKBACK]) / PRICE_HISTORY[-LOOKBACK]
    usd_balance = check_balance("USD")
    crypto_balance = check_balance(TRADING_SYMBOL.split("-")[0])

    if momentum <= -MOMENTUM_THRESHOLD and usd_balance >= TRADE_AMOUNT:
        place_order("buy", TRADING_SYMBOL, TRADE_AMOUNT)
    elif momentum >= MOMENTUM_THRESHOLD and crypto_balance > 0:
        place_order("sell", TRADING_SYMBOL, crypto_balance)

    if len(PRICE_HISTORY) > LOOKBACK:
        PRICE_HISTORY.pop(0)

# ======================
# MAIN LOOP
# ======================
while True:
    try:
        price = get_price(TRADING_SYMBOL)
        print(f"[{datetime.now()}] Current price of {TRADING_SYMBOL}: ${price}")
        nija_strategy(price)
        time.sleep(SLEEP_INTERVAL)
    except Exception as e:
        print(f"[{datetime.now()}] Error: {e}")
        time.sleep(SLEEP_INTERVAL)
