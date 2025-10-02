import coinbase_advanced_py as cb
import time

# ======================
# CONFIG
# ======================
api_key = "f0e7ae67-cf8a-4aee-b3cd-17227a1b8267"
api_secret = "nMHcCAQEEIHVW3T1TLBFLjoNqDOsQjtPtny50auqVT1Y27fIyefOcoAoGCCqGSM49"
SANDBOX = False  # True = test environment, False = live trading
TRADING_SYMBOL = "BTC-USD"  # Example: BTC-USD, ETH-USD
TRADE_AMOUNT = 10  # USD per trade
BUY_THRESHOLD = 30000  # Buy when price <= this
SELL_THRESHOLD = 35000  # Sell when price >= this
SLEEP_INTERVAL = 10  # Seconds between checks

# ======================
# CONNECT TO COINBASE
# ======================
try:
    client = cb.CoinbaseAdvanced(api_key=api_key, api_secret=api_secret, sandbox=SANDBOX)
    print("✅ Connected to Coinbase Advanced")
except Exception as e:
    print("❌ Failed to connect to Coinbase:", e)
    exit(1)

# ======================
# FUNCTION TO CHECK BALANCE
# ======================
def check_balance(currency="USD"):
    try:
        balances = client.get_accounts()
        for b in balances:
            if b['currency'] == currency:
                return float(b['balance'])
    except Exception as e:
        print(f"❌ Error checking {currency} balance:", e)
    return 0.0

# ======================
# FUNCTION TO GET CURRENT PRICE
# ======================
def get_price(symbol):
    try:
        ticker = client.get_product_ticker(symbol)
        return float(ticker['price'])
    except Exception as e:
        print(f"❌ Error fetching price for {symbol}:", e)
        return 0.0

# ======================
# PLACE BUY ORDER
# ======================
def place_buy(symbol, amount):
    print(f"📈 Placing BUY order for ${amount} of {symbol}")
    try:
        order = client.place_order(
            product_id=symbol,
            side="buy",
            order_type="market",
            funds=str(amount)
        )
        print("✅ BUY order successful:", order)
    except Exception as e:
        print("❌ BUY order failed:", e)

# ======================
# PLACE SELL ORDER
# ======================
def place_sell(symbol, amount):
    print(f"📉 Placing SELL order for {amount} {symbol.split('-')[0]}")
    try:
        order = client.place_order(
            product_id=symbol,
            side="sell",
            order_type="market",
            funds=str(amount)
        )
        print("✅ SELL order successful:", order)
    except Exception as e:
        print("❌ SELL order failed:", e)

# ======================
# SIMPLE TRADING LOOP
# ======================
while True:
    try:
        price = get_price(TRADING_SYMBOL)
        if price == 0.0:
            print("⚠ Skipping this loop due to price fetch error")
            time.sleep(SLEEP_INTERVAL)
            continue

        print(f"💲 Current price of {TRADING_SYMBOL}: ${price}")

        usd_balance = check_balance("USD")
        crypto_balance = check_balance(TRADING_SYMBOL.split("-")[0])

        print(f"💰 USD Balance: ${usd_balance}, Crypto Balance: {crypto_balance} {TRADING_SYMBOL.split('-')[0]}")

        # Buy if price is below threshold
        if price <= BUY_THRESHOLD and usd_balance >= TRADE_AMOUNT:
            place_buy(TRADING_SYMBOL, TRADE_AMOUNT)

        # Sell if price is above threshold
        elif price >= SELL_THRESHOLD and crypto_balance > 0:
            place_sell(TRADING_SYMBOL, crypto_balance)

        time.sleep(SLEEP_INTERVAL)

    except Exception as e:
        print("❌ Error in trading loop:", e)
        time.sleep(SLEEP_INTERVAL)
