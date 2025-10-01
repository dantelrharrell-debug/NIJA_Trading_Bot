import time
import coinbase_advanced_py as cb
import os

# ======================
# CONFIG
# ======================
API_KEY = os.getenv("API_KEY")  # safer to use environment variables
API_SECRET = os.getenv("API_SECRET")
SANDBOX = True  # Set to False for live trading
TRADING_SYMBOL = "BTC-USD"  # Example: BTC-USD, ETH-USD
TRADE_AMOUNT = 10  # USD amount per trade
BUY_THRESHOLD = 30000  # Price to trigger buy
SELL_THRESHOLD = 35000  # Price to trigger sell
SLEEP_INTERVAL = 10  # Seconds between each check

# ======================
# CONNECT TO COINBASE
# ======================
client = cb.CoinbaseAdvanced(api_key=API_KEY, api_secret=API_SECRET, sandbox=SANDBOX)
print("Connected to Coinbase Advanced")

# ======================
# FUNCTION TO CHECK BALANCE
# ======================
def check_balance(currency="USD"):
    balances = client.get_accounts()
    for b in balances:
        if b['currency'] == currency:
            return float(b['balance'])
    return 0.0

# ======================
# FUNCTION TO GET CURRENT PRICE
# ======================
def get_price(symbol):
    ticker = client.get_product_ticker(symbol)
    return float(ticker['price'])

# ======================
# PLACE BUY ORDER
# ======================
def place_buy(symbol, amount):
    print(f"Placing BUY order for {amount} USD of {symbol}")
    order = client.place_order(product_id=symbol, side="buy", order_type="market", funds=str(amount))
    print("BUY order details:", order)

# ======================
# PLACE SELL ORDER
# ======================
def place_sell(symbol, amount):
    print(f"Placing SELL order for {amount} USD of {symbol}")
    order = client.place_order(product_id=symbol, side="sell", order_type="market", funds=str(amount))
    print("SELL order details:", order)

# ======================
# SIMPLE TRADING LOOP
# ======================
if __name__ == "__main__":
    while True:
        try:
            price = get_price(TRADING_SYMBOL)
            print(f"Current price of {TRADING_SYMBOL}: ${price}")

            usd_balance = check_balance("USD")
            crypto_balance = check_balance(TRADING_SYMBOL.split("-")[0])

            # Simple strategy
            if price <= BUY_THRESHOLD and usd_balance >= TRADE_AMOUNT:
                place_buy(TRADING_SYMBOL, TRADE_AMOUNT)

            elif price >= SELL_THRESHOLD and crypto_balance > 0:
                place_sell(TRADING_SYMBOL, crypto_balance)

            time.sleep(SLEEP_INTERVAL)

        except Exception as e:
            print("Error:", e)
            time.sleep(SLEEP_INTERVAL)
